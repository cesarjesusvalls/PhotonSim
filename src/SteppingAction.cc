//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .  These *
// * include a list of copyright holders.                             *
// *                                                                  *
// * Neither the authors of this software system, nor their employing *
// * institutes,nor the agencies providing financial support for this *
// * work  make  any representation or  warranty, express or implied, *
// * regarding  this  software system or assume any liability for its *
// * use.  Please see the license in the file  LICENSE  and URL above *
// * for the full disclaimer and the limitation of liability.         *
// *                                                                  *
// * This  code  implementation is the result of  the  scientific and *
// * technical work of the GEANT4 collaboration.                      *
// * By using,  copying,  modifying or  distributing the software (or *
// * any work based  on the software)  you  agree  to acknowledge its *
// * use  in  resulting  scientific  publications,  and indicate your *
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
//
/// \file PhotonSim/src/SteppingAction.cc
/// \brief Implementation of the PhotonSim::SteppingAction class

#include "SteppingAction.hh"
#include "DetectorConstruction.hh"
#include "EventAction.hh"
#include "DataManager.hh"

#include "G4Event.hh"
#include "G4LogicalVolume.hh"
#include "G4RunManager.hh"
#include "G4Step.hh"
#include "G4Track.hh"
#include "G4ParticleDefinition.hh"
#include "G4OpticalPhoton.hh"
#include "G4VProcess.hh"
#include "G4SystemOfUnits.hh"

namespace PhotonSim
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

SteppingAction::SteppingAction(EventAction* eventAction) : fEventAction(eventAction) {}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void SteppingAction::UserSteppingAction(const G4Step* step)
{
  // Get the track and particle information
  G4Track* track = step->GetTrack();
  G4ParticleDefinition* particle = track->GetDefinition();
  
  DataManager* dataManager = DataManager::GetInstance();
  
  // Register all new tracks (first step) for parent tracking
  if (track->GetCurrentStepNumber() == 1) {
    G4int trackID = track->GetTrackID();
    G4String particleName = particle->GetParticleName();
    G4int parentID = track->GetParentID();
    dataManager->RegisterTrack(trackID, particleName, parentID);
  }
  
  // Check if this is an optical photon on its first step (creation)
  if (particle == G4OpticalPhoton::OpticalPhotonDefinition()) {
    // Only record optical photons at their first step (when they're created)
    if (track->GetCurrentStepNumber() == 1) {
      
      // Get the creation process from the track
      const G4VProcess* creationProcess = track->GetCreatorProcess();
      G4String processName = "Unknown";
      if (creationProcess) {
        processName = creationProcess->GetProcessName();
      }
      
      // Get the parent particle information using our track registry
      G4String parentParticle = "Unknown";
      G4int parentID = track->GetParentID();
      
      if (parentID == 0) {
        // Primary particle (original muon)
        parentParticle = "Primary";
      } else {
        // Look up the parent particle name from our registry
        parentParticle = dataManager->GetParticleNameFromTrackID(parentID);
        if (parentParticle == "Unknown") {
          parentParticle = "Secondary_ID_" + std::to_string(parentID);
        }
      }
      
      // Store ALL photons for investigation (no filtering)
      
      // Get position and direction at creation
      // Use vertex position (where photon was actually created) instead of current position
      G4ThreeVector position = track->GetVertexPosition();
      G4ThreeVector direction = track->GetVertexMomentumDirection();
      G4double time = track->GetGlobalTime();
      
      // Record this optical photon using DataManager
      G4int trackID = track->GetTrackID();
      dataManager->AddOpticalPhoton(position.x(), position.y(), position.z(),
                                   direction.x(), direction.y(), direction.z(),
                                   time, processName, parentParticle,
                                   parentID, trackID);
      
      // Add some debug output (only for first few photons)
      static G4int photonCount = 0;
      if (photonCount < 10) {
        G4cout << "Optical Photon " << photonCount << " Created by " << processName 
               << " (parent: " << parentParticle << ") at (" 
               << position.x()/mm << ", " << position.y()/mm << ", " << position.z()/mm 
               << ") mm" << G4endl;
        photonCount++;
      }
    }
    return; // Don't process further for optical photons
  }
  
  // Debug: Track charged particles to see what's creating Cherenkov light
  if (particle->GetPDGCharge() != 0) {
    static G4int particleStepCount = 0;
    if (particleStepCount < 20) {
      G4ThreeVector pos = track->GetPosition();
      G4double distance = sqrt(pos.x()*pos.x() + pos.y()*pos.y() + pos.z()*pos.z());
      G4cout << "Charged particle: " << particle->GetParticleName() 
             << " at (" << pos.x()/mm << ", " << pos.y()/mm << ", " << pos.z()/mm 
             << ") mm, distance=" << distance/mm << "mm, energy=" 
             << track->GetKineticEnergy()/MeV << " MeV" << G4endl;
      particleStepCount++;
    }
  }
  
  // Also collect energy deposition in the detector volume for general tracking
  if (!fDetectorVolume) {
    const auto detConstruction = static_cast<const DetectorConstruction*>(
      G4RunManager::GetRunManager()->GetUserDetectorConstruction());
    fDetectorVolume = detConstruction->GetDetectorVolume();
  }

  // Get volume of the current step
  G4LogicalVolume* volume =
    step->GetPreStepPoint()->GetTouchableHandle()->GetVolume()->GetLogicalVolume();

  // Check if we are in detector volume and collect energy deposition
  if (volume == fDetectorVolume) {
    G4double edepStep = step->GetTotalEnergyDeposit();
    fEventAction->AddEdep(edepStep);
    
    // Store detailed energy deposit information for scintillation analysis
    if (edepStep > 0.0) {
      G4ThreeVector stepPos = step->GetPostStepPoint()->GetPosition();
      G4double stepTime = step->GetPostStepPoint()->GetGlobalTime();
      G4String particleName = particle->GetParticleName();
      G4int trackID = track->GetTrackID();
      G4int parentID = track->GetParentID();
      
      dataManager->AddEnergyDeposit(stepPos.x(), stepPos.y(), stepPos.z(),
                                   edepStep, stepTime, particleName,
                                   trackID, parentID);
      
      // Debug output for first few energy deposits
      static G4int edepCount = 0;
      if (edepCount < 10) {
        G4cout << "Energy Deposit " << edepCount << ": " << edepStep/keV 
               << " keV by " << particleName << " at (" 
               << stepPos.x()/mm << ", " << stepPos.y()/mm << ", " << stepPos.z()/mm 
               << ") mm, t=" << stepTime/ns << " ns" << G4endl;
        edepCount++;
      }
    }
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim