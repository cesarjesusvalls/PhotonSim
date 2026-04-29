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
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
//
/// \file PhotonSim/src/DataManagerMessenger.cc
/// \brief Implementation of the PhotonSim::DataManagerMessenger class

#include "DataManagerMessenger.hh"
#include "DataManager.hh"

#include "G4UIdirectory.hh"
#include "G4UIcmdWithABool.hh"
#include "G4UIcmdWithAString.hh"
#include "G4UImanager.hh"
#include "G4ApplicationState.hh"
#include "G4ios.hh"

namespace PhotonSim
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

DataManagerMessenger::DataManagerMessenger()
{
  fDataManager = DataManager::GetInstance();

  fPhotonDir = new G4UIdirectory("/photon/");
  fPhotonDir->SetGuidance("Commands for photon data control");

  fOutputDir = new G4UIdirectory("/output/");
  fOutputDir->SetGuidance("Commands for output file control");

  fStorePhotonsCmd = new G4UIcmdWithABool("/photon/storeIndividual", this);
  fStorePhotonsCmd->SetGuidance("Enable/disable storage of individual photon data");
  fStorePhotonsCmd->SetGuidance("When disabled, only 2D histograms are filled");
  fStorePhotonsCmd->SetParameterName("store", false);
  fStorePhotonsCmd->SetDefaultValue(true);
  fStorePhotonsCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

  fStoreProcessNameCmd = new G4UIcmdWithABool("/photon/storeProcessName", this);
  fStoreProcessNameCmd->SetGuidance("Enable/disable PhotonProcess branch on OpticalPhotonsRaw");
  fStoreProcessNameCmd->SetGuidance("Stores Geant4 process name per photon (Cerenkov/Scintillation/...).");
  fStoreProcessNameCmd->SetGuidance("Default off — useful only when scintillation/WLS materials are present.");
  fStoreProcessNameCmd->SetParameterName("store", false);
  fStoreProcessNameCmd->SetDefaultValue(false);
  fStoreProcessNameCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

  fStreamPhotonsChunkedCmd = new G4UIcmdWithABool("/photon/streamPhotonsChunked", this);
  fStreamPhotonsChunkedCmd->SetGuidance("Enable/disable mid-event flushing of photon chunks");
  fStreamPhotonsChunkedCmd->SetGuidance("When true (default), photons flush every 100k to OpticalPhotonsRaw");
  fStreamPhotonsChunkedCmd->SetGuidance("so peak vector RAM stays bounded. When false, only flush at EndEvent");
  fStreamPhotonsChunkedCmd->SetGuidance("(one giant chunk per event; same on-disk schema). Debug-only.");
  fStreamPhotonsChunkedCmd->SetParameterName("stream", false);
  fStreamPhotonsChunkedCmd->SetDefaultValue(true);
  fStreamPhotonsChunkedCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

  fEmitRawSegmentsCmd = new G4UIcmdWithABool("/photon/emitRawSegments", this);
  fEmitRawSegmentsCmd->SetGuidance("Enable/disable raw-segment output (skip C++ merger).");
  fEmitRawSegmentsCmd->SetGuidance("When true (default on this branch), every G4 sub-step is its own");
  fEmitRawSegmentsCmd->SetGuidance("Segment_* row; LUCiD reapplies the merger and writes group_id.");
  fEmitRawSegmentsCmd->SetGuidance("When false, today's C++ merger runs (kept for byte-identity A/B).");
  fEmitRawSegmentsCmd->SetParameterName("emit", false);
  fEmitRawSegmentsCmd->SetDefaultValue(true);
  fEmitRawSegmentsCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

  fFilenameCmd = new G4UIcmdWithAString("/output/filename", this);
  fFilenameCmd->SetGuidance("Set output ROOT filename");
  fFilenameCmd->SetGuidance("Must be called before /run/initialize");
  fFilenameCmd->SetParameterName("filename", false);
  fFilenameCmd->SetDefaultValue("optical_photons.root");
  fFilenameCmd->AvailableForStates(G4State_PreInit, G4State_Idle);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

DataManagerMessenger::~DataManagerMessenger()
{
  delete fPhotonDir;
  delete fOutputDir;
  delete fStorePhotonsCmd;
  delete fStoreProcessNameCmd;
  delete fStreamPhotonsChunkedCmd;
  delete fEmitRawSegmentsCmd;
  delete fFilenameCmd;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManagerMessenger::SetNewValue(G4UIcommand* command, G4String newValue)
{
  if (command == fStorePhotonsCmd) {
    bool store = fStorePhotonsCmd->GetNewBoolValue(newValue);
    fDataManager->SetStoreIndividualPhotons(store);
    G4cout << "Individual photon storage: " << (store ? "enabled" : "disabled") << G4endl;
  }

  if (command == fStoreProcessNameCmd) {
    bool store = fStoreProcessNameCmd->GetNewBoolValue(newValue);
    fDataManager->SetStoreProcessName(store);
    G4cout << "Per-photon process name storage: " << (store ? "enabled" : "disabled") << G4endl;
  }

  if (command == fStreamPhotonsChunkedCmd) {
    bool stream = fStreamPhotonsChunkedCmd->GetNewBoolValue(newValue);
    fDataManager->SetStreamPhotonsChunked(stream);
    G4cout << "Chunked photon streaming: " << (stream ? "enabled" : "disabled") << G4endl;
  }

  if (command == fEmitRawSegmentsCmd) {
    bool emit = fEmitRawSegmentsCmd->GetNewBoolValue(newValue);
    fDataManager->SetEmitRawSegments(emit);
    G4cout << "Raw-segment emission (Python-side merger): "
           << (emit ? "enabled" : "disabled (C++ merger active)") << G4endl;
  }

  if (command == fFilenameCmd) {
    fDataManager->SetOutputFilename(newValue);
    G4cout << "Output filename set to: " << newValue << G4endl;
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim
