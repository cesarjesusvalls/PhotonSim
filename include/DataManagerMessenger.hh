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
/// \file PhotonSim/include/DataManagerMessenger.hh
/// \brief Definition of the PhotonSim::DataManagerMessenger class

#ifndef PhotonSimDataManagerMessenger_h
#define PhotonSimDataManagerMessenger_h 1

#include "G4UImessenger.hh"
#include "globals.hh"

class G4UIdirectory;
class G4UIcmdWithABool;
class G4UIcommand;

namespace PhotonSim
{

class DataManager;

/// Messenger class for DataManager settings
///
/// This class defines commands for controlling data storage:
/// - /photon/storeIndividual [true/false]
/// - /edep/storeIndividual [true/false]

class DataManagerMessenger: public G4UImessenger
{
  public:
    DataManagerMessenger();
    ~DataManagerMessenger() override;

    void SetNewValue(G4UIcommand*, G4String) override;

  private:
    DataManager*                   fDataManager = nullptr;

    G4UIdirectory*                 fPhotonDir = nullptr;
    G4UIdirectory*                 fEdepDir = nullptr;
    G4UIcmdWithABool*              fStorePhotonsCmd = nullptr;
    G4UIcmdWithABool*              fStoreEdepsCmd = nullptr;
};

}  // namespace PhotonSim

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#endif