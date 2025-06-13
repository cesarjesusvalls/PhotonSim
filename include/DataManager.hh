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
/// \file PhotonSim/include/DataManager.hh
/// \brief Definition of the PhotonSim::DataManager class

#ifndef OpticalDataManager_h
#define OpticalDataManager_h 1

#include "G4String.hh"
#include "G4Types.hh"
#include <vector>
#include <memory>

class TFile;
class TTree;

namespace PhotonSim
{

/// Singleton class to manage ROOT data output for optical photons

class DataManager
{
  public:
    static DataManager* GetInstance();
    
    void Initialize(const G4String& filename);
    void Finalize();
    
    void BeginEvent(G4int eventID, G4double primaryEnergy);
    void EndEvent();
    
    void AddOpticalPhoton(G4double x, G4double y, G4double z,
                         G4double dx, G4double dy, G4double dz,
                         G4double time, const G4String& process);
    
  private:
    DataManager() = default;
    ~DataManager() = default;
    
    static DataManager* fInstance;
    
    std::unique_ptr<TFile> fRootFile;
    TTree* fTree = nullptr;
    
    // Event-level data
    G4int fEventID = 0;
    G4double fPrimaryEnergy = 0.0;
    G4int fNOpticalPhotons = 0;
    
    // Optical photon data (vectors for multiple photons per event)
    std::vector<G4double> fPhotonPosX;
    std::vector<G4double> fPhotonPosY;
    std::vector<G4double> fPhotonPosZ;
    std::vector<G4double> fPhotonDirX;
    std::vector<G4double> fPhotonDirY;
    std::vector<G4double> fPhotonDirZ;
    std::vector<G4double> fPhotonTime;
    std::vector<G4String> fPhotonProcess;
    
    void ClearEventData();
};

}  // namespace PhotonSim

#endif