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
/// \file PhotonSim/include/RandomSeedMessenger.hh
/// \brief Definition of the PhotonSim::RandomSeedMessenger class

#ifndef PhotonSimRandomSeedMessenger_h
#define PhotonSimRandomSeedMessenger_h 1

#include "G4UImessenger.hh"
#include "globals.hh"

class G4UIdirectory;
class G4UIcommand;

namespace PhotonSim
{

/// Messenger class for random seed control
///
/// This class defines commands for controlling random number generation:
/// - /random/setSeed [seed1] [seed2]
///
/// If not called, automatic seeding based on current time is used.

class RandomSeedMessenger: public G4UImessenger
{
  public:
    RandomSeedMessenger();
    ~RandomSeedMessenger() override;

    void SetNewValue(G4UIcommand*, G4String) override;

    // Check if seeds were set via macro
    bool SeedsWereSet() const { return fSeedsSet; }
    long GetSeed1() const { return fSeed1; }
    long GetSeed2() const { return fSeed2; }

  private:
    G4UIdirectory*  fRandomDir = nullptr;
    G4UIcommand*    fSetSeedCmd = nullptr;

    bool fSeedsSet = false;
    long fSeed1 = 0;
    long fSeed2 = 0;
};

}  // namespace PhotonSim

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#endif
