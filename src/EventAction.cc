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
/// \file PhotonSim/src/EventAction.cc
/// \brief Implementation of the PhotonSim::EventAction class

#include "EventAction.hh"
#include "RunAction.hh"
#include "DataManager.hh"
#include "PrimaryGeneratorAction.hh"

#include "G4Event.hh"
#include "G4RunManager.hh"
#include <iomanip>

namespace PhotonSim
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

EventAction::EventAction(RunAction* runAction) : fRunAction(runAction) {}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void EventAction::BeginOfEventAction(const G4Event* event)
{
  fEdep = 0.;
  
  // Initialize start time on first event
  if (event->GetEventID() == 0) {
    fStartTime = std::chrono::steady_clock::now();
  }
  
  // Get primary particle energy from the generator
  const auto primaryGenerator = static_cast<const PrimaryGeneratorAction*>(
    G4RunManager::GetRunManager()->GetUserPrimaryGeneratorAction());
  G4double primaryEnergy = primaryGenerator->GetTrueEnergy();
  
  // Notify DataManager about the beginning of a new event
  DataManager* dataManager = DataManager::GetInstance();
  dataManager->BeginEvent(event->GetEventID(), primaryEnergy);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void EventAction::EndOfEventAction(const G4Event* event)
{
  // accumulate statistics in run action
  fRunAction->AddEdep(fEdep);

  // Notify DataManager about the end of the event
  DataManager* dataManager = DataManager::GetInstance();
  dataManager->EndEvent();

  // Debug pion summary
  static G4bool debugPions = std::getenv("DEBUG_PIONS") != nullptr;
  if (debugPions) {
    dataManager->PrintPionSummary(event->GetEventID());
  }

  // Progress reporting
  G4int eventID = event->GetEventID();
  G4int totalEvents = fRunAction->GetNumberOfEvents();
  
  // Print progress at regular intervals
  if (totalEvents > 0) {
    G4int progressInterval = 1; 
    if (progressInterval == 0) progressInterval = 1;
    
    if (eventID % progressInterval == 0 || eventID == totalEvents - 1) {
      G4double progress = 100.0 * (eventID) / totalEvents;
      G4cout << "\rProgress: [";
      
      // Draw progress bar
      G4int barWidth = 40;
      G4int pos = barWidth * progress / 100.0;
      for (G4int i = 0; i < barWidth; ++i) {
        if (i < pos) G4cout << "=";
        else if (i == pos) G4cout << ">";
        else G4cout << " ";
      }
      
      // Calculate elapsed time and ETA
      auto currentTime = std::chrono::steady_clock::now();
      auto elapsedSeconds = std::chrono::duration_cast<std::chrono::seconds>(currentTime - fStartTime).count();
      
      // Format elapsed time
      G4int elapsedHours = elapsedSeconds / 3600;
      G4int elapsedMinutes = (elapsedSeconds % 3600) / 60;
      G4int elapsedSecs = elapsedSeconds % 60;
      
      G4cout << "] " << std::fixed << std::setprecision(1) 
             << progress << "% (" << eventID << "/" << totalEvents << ")";
      
      // Show elapsed time
      G4cout << " Elapsed: ";
      if (elapsedHours > 0) {
        G4cout << elapsedHours << "h " << elapsedMinutes << "m " << elapsedSecs << "s";
      } else if (elapsedMinutes > 0) {
        G4cout << elapsedMinutes << "m " << elapsedSecs << "s";
      } else {
        G4cout << elapsedSecs << "s";
      }
      
      // Calculate and show ETA (only if we've processed at least one event)
      if (eventID > 0) {
        G4double secondsPerEvent = static_cast<G4double>(elapsedSeconds) / eventID;
        G4int remainingEvents = totalEvents - eventID;
        G4int remainingSeconds = static_cast<G4int>(secondsPerEvent * remainingEvents);
        
        G4int etaHours = remainingSeconds / 3600;
        G4int etaMinutes = (remainingSeconds % 3600) / 60;
        G4int etaSecs = remainingSeconds % 60;
        
        G4cout << " ETA: ";
        if (etaHours > 0) {
          G4cout << etaHours << "h " << etaMinutes << "m " << etaSecs << "s";
        } else if (etaMinutes > 0) {
          G4cout << etaMinutes << "m " << etaSecs << "s";
        } else {
          G4cout << etaSecs << "s";
        }
      }
      
      G4cout << "     " << std::flush;
      
      // Print newline when complete
      if (eventID == totalEvents - 1) {
        G4cout << G4endl;
      }
    }
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim
