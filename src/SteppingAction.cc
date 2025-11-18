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
#include "G4PhysicalConstants.hh"

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

  // Register all new tracks (first step) with full information
  if (track->GetCurrentStepNumber() == 1) {
    G4int trackID = track->GetTrackID();
    G4String particleName = particle->GetParticleName();
    G4int parentID = track->GetParentID();
    G4ThreeVector position = track->GetVertexPosition();
    G4ThreeVector momentum = track->GetMomentum();
    G4double energy = track->GetKineticEnergy();
    G4double time = track->GetGlobalTime() - step->GetDeltaTime();
    G4int pdgCode = particle->GetPDGEncoding();

    dataManager->RegisterTrack(trackID, particleName, parentID, position, momentum, energy, time, pdgCode);

    // Category classification logic
    const G4VProcess* creationProcess = track->GetCreatorProcess();
    G4String processName = creationProcess ? creationProcess->GetProcessName() : "Primary";

    // 1. Primary particles (parentID == 0)
    if (parentID == 0) {
      G4int subID = dataManager->GetNextPrimaryID();
      dataManager->UpdateTrackCategory(trackID, kPrimary, subID, 0);
    }

    // 2. Decay electrons: electrons from Decay or muMinusCaptureAtRest process
    else if (particleName == "e-" || particleName == "e+") {
      // Accept electrons from both free decay and bound muon decay
      // - "Decay": free muon/pion decay
      // - "muMinusCaptureAtRest": bound muon decay (~80-90% branch) or nuclear capture (10-20% - no electron)
      if (processName == "Decay" || processName == "muMinusCaptureAtRest") {
        // Check DIRECT parent is muon or pion
        TrackInfo* parentInfo = dataManager->GetTrackInfo(parentID);
        if (parentInfo && (parentInfo->particleName == "mu-" || parentInfo->particleName == "mu+" ||
                           parentInfo->particleName == "pi-" || parentInfo->particleName == "pi+")) {
          // Apply energy threshold to exclude Auger electrons from muonic atom de-excitation
          // and other low-energy secondaries (typically eV-keV range)
          if (energy > 1.0 * MeV) {
            // Assign new decay electron SubID using DIRECT parent
            G4int subID = dataManager->GetNextDecayElectronID();
            dataManager->UpdateTrackCategory(trackID, kDecayElectron, subID, parentID);
          }
        }
      }
    }

    // 3. Gamma showers: gammas from pi0 decay
    else if (particleName == "gamma") {
      if (processName == "Decay") {
        TrackInfo* parentInfo = dataManager->GetTrackInfo(parentID);
        if (parentInfo && parentInfo->particleName == "pi0") {
          // Assign new gamma shower SubID
          G4int subID = dataManager->GetNextGammaShowerID();
          dataManager->UpdateTrackCategory(trackID, kGammaShower, subID, parentID);
        }
      }
    }
  }

  // 4. Secondary pion deflection detection: check for inelastic interactions
  G4String particleName = particle->GetParticleName();
  if (particleName == "pi+" || particleName == "pi-") {
    const G4VProcess* process = step->GetPostStepPoint()->GetProcessDefinedStep();
    if (process) {
      G4String currentProcessName = process->GetProcessName();
      // Check for inelastic processes
      if (currentProcessName.contains("Inelastic") || currentProcessName.contains("inelastic")) {
        G4int trackID = track->GetTrackID();
        TrackInfo* info = dataManager->GetTrackInfo(trackID);
        if (info) {
          // Compare pre-step and post-step momentum directions
          G4ThreeVector postMomentum = track->GetMomentumDirection();
          G4double angle = std::acos(info->preMomentumDir.dot(postMomentum));

          // If deflection > 20 degrees, create new secondary pion instance
          if (angle > 20.0 * deg) {
            // Find the category-relevant parent
            G4int categoryParent = info->parentTrackID;
            TrackInfo* parentInfo = dataManager->GetTrackInfo(categoryParent);
            while (parentInfo && parentInfo->category < 0 && parentInfo->parentTrackID > 0) {
              categoryParent = parentInfo->parentTrackID;
              parentInfo = dataManager->GetTrackInfo(categoryParent);
            }

            G4int subID = dataManager->GetNextSecondaryPionID();
            dataManager->UpdateTrackCategory(trackID, kSecondaryPion, subID, categoryParent);
          }

          // Update momentum for next check
          dataManager->UpdatePionMomentum(trackID, track->GetMomentum());
        }
      }
    }
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

      // Find category-relevant parent by tracing back through ancestry
      G4int parentID = track->GetParentID();
      G4int categoryParentID = parentID;
      TrackInfo* parentInfo = dataManager->GetTrackInfo(parentID);

      // Trace back to find most recent categorized ancestor
      while (parentInfo && parentInfo->category < 0 && parentInfo->parentTrackID > 0) {
        categoryParentID = parentInfo->parentTrackID;
        parentInfo = dataManager->GetTrackInfo(categoryParentID);
      }

      // Build genealogy using the DataManager method
      std::vector<G4int> genealogy = dataManager->BuildGenealogy(categoryParentID);

      // Get position and direction at creation
      G4ThreeVector position = track->GetVertexPosition();
      G4ThreeVector direction = track->GetVertexMomentumDirection();
      G4double time = track->GetGlobalTime() - step->GetDeltaTime();

      // Calculate wavelength from photon energy
      G4double photonEnergy = track->GetKineticEnergy();
      G4double wavelength = (h_Planck * c_light) / photonEnergy;

      // Record this optical photon with genealogy
      dataManager->AddOpticalPhoton(position.x(), position.y(), position.z(),
                                   direction.x(), direction.y(), direction.z(),
                                   time, wavelength, processName,
                                   genealogy);
    }
    return; // Don't process further for optical photons
  }
  
  // Debug prints removed
  
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
      
      // Debug prints removed
    }
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim