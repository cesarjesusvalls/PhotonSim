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
      
      // Get position and direction at creation
      G4ThreeVector position = track->GetPosition();
      G4ThreeVector direction = track->GetMomentumDirection();
      G4double time = track->GetGlobalTime();
      
      // Record this optical photon using DataManager
      DataManager* dataManager = DataManager::GetInstance();
      dataManager->AddOpticalPhoton(position.x(), position.y(), position.z(),
                                   direction.x(), direction.y(), direction.z(),
                                   time, processName);
      
      // Add some debug output
      G4cout << "Optical Photon Created by " << processName << " at (" 
             << position.x()/mm << ", " << position.y()/mm << ", " << position.z()/mm 
             << ") mm" << G4endl;
    }
    return; // Don't process further for optical photons
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
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim