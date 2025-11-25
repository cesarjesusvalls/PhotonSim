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
#include "G4UIcmdWithABool.hh"
#include "G4UIcmdWithAnInteger.hh"
#include "G4UIcmdWithoutParameter.hh"
#include "G4UIcommand.hh"
#include "G4UIparameter.hh"
#include "G4SystemOfUnits.hh"
#include <sstream>

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

  fRandomEnergyCmd = new G4UIcmdWithABool("/gun/randomEnergy", this);
  fRandomEnergyCmd->SetGuidance("Enable/disable random energy generation");
  fRandomEnergyCmd->SetGuidance("If true, energy is randomly chosen from the specified range");
  fRandomEnergyCmd->SetGuidance("If false, uses the fixed energy set by /gun/energy");
  fRandomEnergyCmd->SetParameterName("useRandom", false);
  fRandomEnergyCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

  fEnergyMinCmd = new G4UIcmdWithADoubleAndUnit("/gun/energyMin", this);
  fEnergyMinCmd->SetGuidance("Set minimum energy for random energy generation");
  fEnergyMinCmd->SetGuidance("Only used when /gun/randomEnergy is set to true");
  fEnergyMinCmd->SetParameterName("minEnergy", false);
  fEnergyMinCmd->SetDefaultUnit("MeV");
  fEnergyMinCmd->SetUnitCandidates("eV keV MeV GeV TeV");
  fEnergyMinCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

  fEnergyMaxCmd = new G4UIcmdWithADoubleAndUnit("/gun/energyMax", this);
  fEnergyMaxCmd->SetGuidance("Set maximum energy for random energy generation");
  fEnergyMaxCmd->SetGuidance("Only used when /gun/randomEnergy is set to true");
  fEnergyMaxCmd->SetParameterName("maxEnergy", false);
  fEnergyMaxCmd->SetDefaultUnit("MeV");
  fEnergyMaxCmd->SetUnitCandidates("eV keV MeV GeV TeV");
  fEnergyMaxCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

  fRandomDirectionCmd = new G4UIcmdWithABool("/gun/randomDirection", this);
  fRandomDirectionCmd->SetGuidance("Enable/disable random direction generation");
  fRandomDirectionCmd->SetGuidance("If true, each primary is fired in a random direction (isotropic on sphere)");
  fRandomDirectionCmd->SetGuidance("If false, uses the fixed direction set by /gun/direction (default: 0 0 1)");
  fRandomDirectionCmd->SetParameterName("useRandom", false);
  fRandomDirectionCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

  fNumberOfPrimariesCmd = new G4UIcmdWithAnInteger("/gun/numberOfPrimaries", this);
  fNumberOfPrimariesCmd->SetGuidance("Set number of primary particles per event");
  fNumberOfPrimariesCmd->SetParameterName("n", false);
  fNumberOfPrimariesCmd->SetRange("n>=1");
  fNumberOfPrimariesCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

  // Command to add a primary particle to the heterogeneous list
  fAddPrimaryCmd = new G4UIcommand("/gun/addPrimary", this);
  fAddPrimaryCmd->SetGuidance("Add a primary particle to the heterogeneous list");
  fAddPrimaryCmd->SetGuidance("Usage: /gun/addPrimary [particleName] [energy] [unit]");
  fAddPrimaryCmd->SetGuidance("Example: /gun/addPrimary mu- 1000 MeV");

  G4UIparameter* particleParam = new G4UIparameter("particleName", 's', false);
  particleParam->SetGuidance("Particle name (e.g., mu-, pi+, e-, proton)");
  fAddPrimaryCmd->SetParameter(particleParam);

  G4UIparameter* energyParam = new G4UIparameter("energy", 'd', false);
  energyParam->SetGuidance("Energy value");
  fAddPrimaryCmd->SetParameter(energyParam);

  G4UIparameter* unitParam = new G4UIparameter("unit", 's', false);
  unitParam->SetGuidance("Energy unit (eV, keV, MeV, GeV, TeV)");
  unitParam->SetDefaultValue("MeV");
  fAddPrimaryCmd->SetParameter(unitParam);

  fAddPrimaryCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

  // Command to add a primary particle with random energy range
  fAddPrimaryWithEnergyRangeCmd = new G4UIcommand("/gun/addPrimaryWithEnergyRange", this);
  fAddPrimaryWithEnergyRangeCmd->SetGuidance("Add a primary particle with random energy from a range");
  fAddPrimaryWithEnergyRangeCmd->SetGuidance("Usage: /gun/addPrimaryWithEnergyRange [particleName] [minEnergy] [maxEnergy] [unit]");
  fAddPrimaryWithEnergyRangeCmd->SetGuidance("Example: /gun/addPrimaryWithEnergyRange mu- 105 1500 MeV");

  G4UIparameter* particleParamRange = new G4UIparameter("particleName", 's', false);
  particleParamRange->SetGuidance("Particle name (e.g., mu-, pi+, e-, proton)");
  fAddPrimaryWithEnergyRangeCmd->SetParameter(particleParamRange);

  G4UIparameter* minEnergyParam = new G4UIparameter("minEnergy", 'd', false);
  minEnergyParam->SetGuidance("Minimum energy value");
  fAddPrimaryWithEnergyRangeCmd->SetParameter(minEnergyParam);

  G4UIparameter* maxEnergyParam = new G4UIparameter("maxEnergy", 'd', false);
  maxEnergyParam->SetGuidance("Maximum energy value");
  fAddPrimaryWithEnergyRangeCmd->SetParameter(maxEnergyParam);

  G4UIparameter* unitParamRange = new G4UIparameter("unit", 's', false);
  unitParamRange->SetGuidance("Energy unit (eV, keV, MeV, GeV, TeV)");
  unitParamRange->SetDefaultValue("MeV");
  fAddPrimaryWithEnergyRangeCmd->SetParameter(unitParamRange);

  fAddPrimaryWithEnergyRangeCmd->AvailableForStates(G4State_PreInit, G4State_Idle);

  // Command to clear the heterogeneous primary list
  fClearPrimariesCmd = new G4UIcmdWithoutParameter("/gun/clearPrimaries", this);
  fClearPrimariesCmd->SetGuidance("Clear the heterogeneous primary particle list");
  fClearPrimariesCmd->AvailableForStates(G4State_PreInit, G4State_Idle);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

PrimaryGeneratorMessenger::~PrimaryGeneratorMessenger()
{
  delete fParticleCmd;
  delete fEnergyCmd;
  delete fPositionCmd;
  delete fDirectionCmd;
  delete fRandomEnergyCmd;
  delete fEnergyMinCmd;
  delete fEnergyMaxCmd;
  delete fRandomDirectionCmd;
  delete fNumberOfPrimariesCmd;
  delete fAddPrimaryCmd;
  delete fAddPrimaryWithEnergyRangeCmd;
  delete fClearPrimariesCmd;
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
  else if (command == fRandomEnergyCmd) {
    fPrimaryGeneratorAction->SetRandomEnergy(fRandomEnergyCmd->GetNewBoolValue(newValue));
  }
  else if (command == fEnergyMinCmd) {
    G4double currentMax = fPrimaryGeneratorAction->GetMaxEnergy();
    G4double newMin = fEnergyMinCmd->GetNewDoubleValue(newValue);
    fPrimaryGeneratorAction->SetEnergyRange(newMin, currentMax);
  }
  else if (command == fEnergyMaxCmd) {
    G4double currentMin = fPrimaryGeneratorAction->GetMinEnergy();
    G4double newMax = fEnergyMaxCmd->GetNewDoubleValue(newValue);
    fPrimaryGeneratorAction->SetEnergyRange(currentMin, newMax);
  }
  else if (command == fRandomDirectionCmd) {
    fPrimaryGeneratorAction->SetRandomDirection(fRandomDirectionCmd->GetNewBoolValue(newValue));
  }
  else if (command == fNumberOfPrimariesCmd) {
    fPrimaryGeneratorAction->SetNumberOfPrimaries(fNumberOfPrimariesCmd->GetNewIntValue(newValue));
  }
  else if (command == fAddPrimaryCmd) {
    // Parse the command parameters: particleName energy unit
    std::istringstream iss(newValue);
    G4String particleName;
    G4double energy;
    G4String unit;

    iss >> particleName >> energy >> unit;

    // Convert energy to internal units
    G4double energyValue = energy;
    if (unit == "eV") energyValue *= eV;
    else if (unit == "keV") energyValue *= keV;
    else if (unit == "MeV") energyValue *= MeV;
    else if (unit == "GeV") energyValue *= GeV;
    else if (unit == "TeV") energyValue *= TeV;

    fPrimaryGeneratorAction->AddPrimary(particleName, energyValue);
  }
  else if (command == fAddPrimaryWithEnergyRangeCmd) {
    // Parse the command parameters: particleName minEnergy maxEnergy unit
    std::istringstream issRange(newValue);
    G4String particleName;
    G4double minEnergy, maxEnergy;
    G4String unit;

    issRange >> particleName >> minEnergy >> maxEnergy >> unit;

    // Convert energies to internal units
    G4double unitFactor = 1.0;
    if (unit == "eV") unitFactor = eV;
    else if (unit == "keV") unitFactor = keV;
    else if (unit == "MeV") unitFactor = MeV;
    else if (unit == "GeV") unitFactor = GeV;
    else if (unit == "TeV") unitFactor = TeV;

    fPrimaryGeneratorAction->AddPrimaryWithEnergyRange(particleName, minEnergy * unitFactor, maxEnergy * unitFactor);
  }
  else if (command == fClearPrimariesCmd) {
    fPrimaryGeneratorAction->ClearPrimaries();
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim