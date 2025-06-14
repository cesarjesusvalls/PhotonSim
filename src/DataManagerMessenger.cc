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
  
  fEdepDir = new G4UIdirectory("/edep/");
  fEdepDir->SetGuidance("Commands for energy deposit data control");
  
  fStorePhotonsCmd = new G4UIcmdWithABool("/photon/storeIndividual", this);
  fStorePhotonsCmd->SetGuidance("Enable/disable storage of individual photon data");
  fStorePhotonsCmd->SetGuidance("When disabled, only 2D histograms are filled");
  fStorePhotonsCmd->SetParameterName("store", false);
  fStorePhotonsCmd->SetDefaultValue(true);
  fStorePhotonsCmd->AvailableForStates(G4State_PreInit, G4State_Idle);
  
  fStoreEdepsCmd = new G4UIcmdWithABool("/edep/storeIndividual", this);
  fStoreEdepsCmd->SetGuidance("Enable/disable storage of individual energy deposit data");
  fStoreEdepsCmd->SetGuidance("When disabled, only 2D histograms are filled");
  fStoreEdepsCmd->SetParameterName("store", false);
  fStoreEdepsCmd->SetDefaultValue(true);
  fStoreEdepsCmd->AvailableForStates(G4State_PreInit, G4State_Idle);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

DataManagerMessenger::~DataManagerMessenger()
{
  delete fPhotonDir;
  delete fEdepDir;
  delete fStorePhotonsCmd;
  delete fStoreEdepsCmd;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManagerMessenger::SetNewValue(G4UIcommand* command, G4String newValue)
{
  if (command == fStorePhotonsCmd) {
    bool store = fStorePhotonsCmd->GetNewBoolValue(newValue);
    fDataManager->SetStoreIndividualPhotons(store);
    G4cout << "Individual photon storage: " << (store ? "enabled" : "disabled") << G4endl;
  }
  
  if (command == fStoreEdepsCmd) {
    bool store = fStoreEdepsCmd->GetNewBoolValue(newValue);
    fDataManager->SetStoreIndividualEdeps(store);
    G4cout << "Individual energy deposit storage: " << (store ? "enabled" : "disabled") << G4endl;
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim