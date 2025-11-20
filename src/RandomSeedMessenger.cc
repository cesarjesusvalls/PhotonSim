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
/// \file PhotonSim/src/RandomSeedMessenger.cc
/// \brief Implementation of the PhotonSim::RandomSeedMessenger class

#include "RandomSeedMessenger.hh"

#include "G4UIdirectory.hh"
#include "G4UIcommand.hh"
#include "G4UIparameter.hh"
#include "G4ApplicationState.hh"
#include "G4ios.hh"
#include "Randomize.hh"
#include <sstream>

namespace PhotonSim
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

RandomSeedMessenger::RandomSeedMessenger()
{
  fRandomDir = new G4UIdirectory("/random/");
  fRandomDir->SetGuidance("Commands for random number generator control");

  fSetSeedCmd = new G4UIcommand("/random/setSeed", this);
  fSetSeedCmd->SetGuidance("Set random number generator seeds");
  fSetSeedCmd->SetGuidance("Usage: /random/setSeed [seed1] [seed2]");
  fSetSeedCmd->SetGuidance("Both seeds should be positive integers");
  fSetSeedCmd->SetGuidance("If not set, automatic time-based seeding is used");

  G4UIparameter* seed1Param = new G4UIparameter("seed1", 'i', false);
  seed1Param->SetGuidance("First random seed (positive integer)");
  fSetSeedCmd->SetParameter(seed1Param);

  G4UIparameter* seed2Param = new G4UIparameter("seed2", 'i', false);
  seed2Param->SetGuidance("Second random seed (positive integer)");
  fSetSeedCmd->SetParameter(seed2Param);

  fSetSeedCmd->AvailableForStates(G4State_PreInit, G4State_Idle);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

RandomSeedMessenger::~RandomSeedMessenger()
{
  delete fSetSeedCmd;
  delete fRandomDir;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void RandomSeedMessenger::SetNewValue(G4UIcommand* command, G4String newValue)
{
  if (command == fSetSeedCmd) {
    std::istringstream iss(newValue);
    iss >> fSeed1 >> fSeed2;
    fSeedsSet = true;

    // Apply the seeds to CLHEP random engine
    CLHEP::HepRandom::setTheSeeds(new long[2]{fSeed1, fSeed2});

    G4cout << "Random seeds set to: " << fSeed1 << " " << fSeed2 << G4endl;
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim
