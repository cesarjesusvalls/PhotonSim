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
/// \file PhotonSim.cc
/// \brief Main program of the PhotonSim application

#include "ActionInitialization.hh"
#include "DetectorConstruction.hh"
#include "PhysicsList.hh"
#include "DataManager.hh"
#include "DataManagerMessenger.hh"

#include "G4RunManagerFactory.hh"
#include "G4SteppingVerbose.hh"
#include "G4UIExecutive.hh"
#include "G4UImanager.hh"
#include "G4VisExecutive.hh"
#include "Randomize.hh"
#include <chrono>
#include <random>
#include <cstdlib>
#include "TROOT.h"

using namespace PhotonSim;

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

int main(int argc, char** argv)
{
  // Initialize ROOT early and properly to avoid global state conflicts
  gROOT->Reset();
  
  // Detect interactive mode (if no arguments) and define UI session
  G4UIExecutive* ui = nullptr;
  if (argc == 1) {
    ui = new G4UIExecutive(argc, argv);
  }

  // Use G4SteppingVerboseWithUnits
  G4int precision = 4;
  G4SteppingVerbose::UseBestUnit(precision);

  // Set automatic random seeds based on current time
  auto now = std::chrono::high_resolution_clock::now();
  auto duration = now.time_since_epoch();
  auto seed1 = std::chrono::duration_cast<std::chrono::microseconds>(duration).count() % 900000000;
  auto seed2 = std::chrono::duration_cast<std::chrono::nanoseconds>(duration).count() % 900000000;
  
  G4cout << "=== AUTOMATIC RANDOM SEED GENERATION ===" << G4endl;
  G4cout << "Setting random seeds: " << seed1 << " " << seed2 << G4endl;
  CLHEP::HepRandom::setTheSeeds(new long[2]{seed1, seed2});

  // Construct the run manager (single-threaded for stable ROOT output)
  auto runManager = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Serial);

  // Set mandatory initialization classes
  // Detector construction
  runManager->SetUserInitialization(new DetectorConstruction());

  // Physics list with optical processes
  runManager->SetUserInitialization(new PhysicsList());

  // User action initialization
  runManager->SetUserInitialization(new ActionInitialization());

  // Initialize data manager messenger for macro commands (before initialization)
  auto dataManagerMessenger = new DataManagerMessenger();

  // Initialize visualization with the default graphics system
  auto visManager = new G4VisExecutive(argc, argv);
  visManager->Initialize();

  // Get the pointer to the User Interface manager
  auto UImanager = G4UImanager::GetUIpointer();

  // Process macro or start UI session
  if (!ui) {
    // batch mode
    G4String command = "/control/execute ";
    G4String fileName = argv[1];
    UImanager->ApplyCommand(command + fileName);
  }
  else {
    // interactive mode - run a few events for demonstration  
    UImanager->ApplyCommand("/run/initialize");
    UImanager->ApplyCommand("/run/beamOn 3");
  }

  // Job termination
  // Finalize data output before deleting managers
  DataManager* dataManager = DataManager::GetInstance();
  dataManager->Finalize();
  
  // Clean up managers first
  delete dataManagerMessenger;
  delete visManager;
  delete runManager;
  
  if (ui) delete ui;
  
  // Properly destroy the singleton instance to avoid memory leaks
  // and prevent ROOT object conflicts on subsequent runs
  DataManager::DeleteInstance();

  // WORKAROUND: This ROOT installation has global class registry conflicts
  // that cause segfaults during cleanup. Since all simulation data is properly
  // saved before this point, use quick_exit to avoid the problematic cleanup.
  std::quick_exit(0);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......