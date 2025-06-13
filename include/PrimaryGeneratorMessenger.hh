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
/// \file PhotonSim/include/PrimaryGeneratorMessenger.hh
/// \brief Definition of the PhotonSim::PrimaryGeneratorMessenger class

#ifndef PhotonSimPrimaryGeneratorMessenger_h
#define PhotonSimPrimaryGeneratorMessenger_h 1

#include "G4UImessenger.hh"
#include "globals.hh"

class G4UIdirectory;
class G4UIcmdWithAString;
class G4UIcmdWithADoubleAndUnit;
class G4UIcmdWith3VectorAndUnit;
class G4UIcmdWith3Vector;

namespace PhotonSim
{

class PrimaryGeneratorAction;

/// Messenger class for particle gun settings
///
/// This class defines commands for the particle gun:
/// - /gun/particle [particleName]
/// - /gun/energy [value] [unit]
/// - /gun/energyRange [minEnergy] [maxEnergy] [unit]
/// - /gun/position [x] [y] [z] [unit]
/// - /gun/direction [x] [y] [z]

class PrimaryGeneratorMessenger: public G4UImessenger
{
  public:
    PrimaryGeneratorMessenger(PrimaryGeneratorAction*);
    ~PrimaryGeneratorMessenger() override;

    void SetNewValue(G4UIcommand*, G4String) override;

  private:
    PrimaryGeneratorAction*        fPrimaryGeneratorAction = nullptr;

    G4UIdirectory*                 fGunDir = nullptr;
    G4UIcmdWithAString*            fParticleCmd = nullptr;
    G4UIcmdWithADoubleAndUnit*     fEnergyCmd = nullptr;
    G4UIcmdWith3VectorAndUnit*     fPositionCmd = nullptr;
    G4UIcmdWith3Vector*            fDirectionCmd = nullptr;
};

}  // namespace PhotonSim

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#endif