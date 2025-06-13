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
/// \file PhotonSim/src/PhysicsList.cc
/// \brief Implementation of the PhotonSim::PhysicsList class

#include "PhysicsList.hh"

#include "G4DecayPhysics.hh"
#include "G4EmStandardPhysics.hh"
#include "G4EmStandardPhysics_option4.hh"
#include "G4OpticalPhysics.hh"
#include "G4RadioactiveDecayPhysics.hh"
#include "G4HadronElasticPhysics.hh"
#include "G4HadronPhysicsQGSP_BERT.hh"
#include "G4StoppingPhysics.hh"
#include "G4IonPhysics.hh"
#include "G4SystemOfUnits.hh"

namespace PhotonSim
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

PhysicsList::PhysicsList()
{
  SetVerboseLevel(1);

  // Default physics for ordinary matter interactions
  RegisterPhysics(new G4DecayPhysics(0));
  RegisterPhysics(new G4RadioactiveDecayPhysics(0));
  RegisterPhysics(new G4EmStandardPhysics_option4(0));

  // Hadron physics for more complete particle interactions
  RegisterPhysics(new G4HadronElasticPhysics(0));
  RegisterPhysics(new G4StoppingPhysics(0));
  RegisterPhysics(new G4IonPhysics(0));
  RegisterPhysics(new G4HadronPhysicsQGSP_BERT(0));

  // Optical physics - this is crucial for optical photon generation
  RegisterPhysics(new G4OpticalPhysics(0));
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void PhysicsList::SetCuts()
{
  // Set production cuts for gamma, electron, positron and proton
  SetCutsWithDefault();
  
  // Set special cuts for optical photons
  SetCutValue(0.01*mm, "gamma");
  SetCutValue(0.01*mm, "e-");
  SetCutValue(0.01*mm, "e+");
  SetCutValue(0.01*mm, "proton");
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim