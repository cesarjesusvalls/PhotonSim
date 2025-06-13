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
/// \file PhotonSim/src/PrimaryGeneratorMessenger.cc
/// \brief Implementation of the PhotonSim::PrimaryGeneratorMessenger class

#include "PrimaryGeneratorMessenger.hh"
#include "PrimaryGeneratorAction.hh"

#include "G4UIdirectory.hh"
#include "G4UIcmdWithAString.hh"
#include "G4UIcmdWithADoubleAndUnit.hh"
#include "G4UIcmdWith3VectorAndUnit.hh"
#include "G4UIcmdWith3Vector.hh"
#include "G4SystemOfUnits.hh"

namespace PhotonSim
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

PrimaryGeneratorMessenger::PrimaryGeneratorMessenger(PrimaryGeneratorAction* primaryGeneratorAction)
 : fPrimaryGeneratorAction(primaryGeneratorAction)
{
  fGunDir = new G4UIdirectory("/gun/");
  fGunDir->SetGuidance("Particle gun control");

  fParticleCmd = new G4UIcmdWithAString("/gun/particle", this);
  fParticleCmd->SetGuidance("Set particle type");
  fParticleCmd->SetGuidance("Available particles: e-, e+, mu-, mu+, pi-, pi+, proton, neutron, gamma");
  fParticleCmd->SetParameterName("particleName", false);
  fParticleCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

  fEnergyCmd = new G4UIcmdWithADoubleAndUnit("/gun/energy", this);
  fEnergyCmd->SetGuidance("Set particle energy");
  fEnergyCmd->SetParameterName("energy", false);
  fEnergyCmd->SetDefaultUnit("MeV");
  fEnergyCmd->SetUnitCandidates("eV keV MeV GeV TeV");
  fEnergyCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

  fPositionCmd = new G4UIcmdWith3VectorAndUnit("/gun/position", this);
  fPositionCmd->SetGuidance("Set particle gun position");
  fPositionCmd->SetParameterName("X", "Y", "Z", false);
  fPositionCmd->SetDefaultUnit("cm");
  fPositionCmd->SetUnitCandidates("nm um mm cm m km");
  fPositionCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

  fDirectionCmd = new G4UIcmdWith3Vector("/gun/direction", this);
  fDirectionCmd->SetGuidance("Set particle gun direction");
  fDirectionCmd->SetParameterName("X", "Y", "Z", false);
  fDirectionCmd->AvailableForStates(G4State_PreInit, G4State_Idle);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

PrimaryGeneratorMessenger::~PrimaryGeneratorMessenger()
{
  delete fParticleCmd;
  delete fEnergyCmd;
  delete fPositionCmd;
  delete fDirectionCmd;
  delete fGunDir;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void PrimaryGeneratorMessenger::SetNewValue(G4UIcommand* command, G4String newValue)
{
  if (command == fParticleCmd) {
    fPrimaryGeneratorAction->SetParticleType(newValue);
  }
  else if (command == fEnergyCmd) {
    fPrimaryGeneratorAction->SetParticleEnergy(fEnergyCmd->GetNewDoubleValue(newValue));
  }
  else if (command == fPositionCmd) {
    fPrimaryGeneratorAction->SetParticlePosition(fPositionCmd->GetNew3VectorValue(newValue));
  }
  else if (command == fDirectionCmd) {
    fPrimaryGeneratorAction->SetParticleDirection(fDirectionCmd->GetNew3VectorValue(newValue));
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim