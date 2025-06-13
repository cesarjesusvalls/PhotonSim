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
/// \file PhotonSim/src/DataManager.cc
/// \brief Implementation of the PhotonSim::DataManager class

#include "DataManager.hh"

#include "TFile.h"
#include "TTree.h"
#include "G4SystemOfUnits.hh"
#include "G4ios.hh"

namespace PhotonSim
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

DataManager* DataManager::fInstance = nullptr;

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

DataManager* DataManager::GetInstance()
{
  if (!fInstance) {
    fInstance = new DataManager();
  }
  return fInstance;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::Initialize(const G4String& filename)
{
  fRootFile = std::make_unique<TFile>(filename.c_str(), "RECREATE");
  if (!fRootFile || fRootFile->IsZombie()) {
    G4cerr << "Error: Cannot create ROOT file " << filename << G4endl;
    return;
  }
  
  fTree = new TTree("OpticalPhotons", "Optical Photon Data");
  
  // Event-level branches
  fTree->Branch("EventID", &fEventID, "EventID/I");
  fTree->Branch("PrimaryEnergy", &fPrimaryEnergy, "PrimaryEnergy/D");
  fTree->Branch("NOpticalPhotons", &fNOpticalPhotons, "NOpticalPhotons/I");
  fTree->Branch("NEnergyDeposits", &fNEnergyDeposits, "NEnergyDeposits/I");
  
  // Optical photon data branches
  fTree->Branch("PhotonPosX", &fPhotonPosX);
  fTree->Branch("PhotonPosY", &fPhotonPosY);
  fTree->Branch("PhotonPosZ", &fPhotonPosZ);
  fTree->Branch("PhotonDirX", &fPhotonDirX);
  fTree->Branch("PhotonDirY", &fPhotonDirY);
  fTree->Branch("PhotonDirZ", &fPhotonDirZ);
  fTree->Branch("PhotonTime", &fPhotonTime);
  fTree->Branch("PhotonProcess", &fPhotonProcess);
  fTree->Branch("PhotonParent", &fPhotonParent);
  fTree->Branch("PhotonParentID", &fPhotonParentID);
  fTree->Branch("PhotonTrackID", &fPhotonTrackID);
  
  // Energy deposit data branches
  fTree->Branch("EdepPosX", &fEdepPosX);
  fTree->Branch("EdepPosY", &fEdepPosY);
  fTree->Branch("EdepPosZ", &fEdepPosZ);
  fTree->Branch("EdepEnergy", &fEdepEnergy);
  fTree->Branch("EdepTime", &fEdepTime);
  fTree->Branch("EdepParticle", &fEdepParticle);
  fTree->Branch("EdepTrackID", &fEdepTrackID);
  fTree->Branch("EdepParentID", &fEdepParentID);
  
  G4cout << "ROOT file " << filename << " created for optical photon and energy deposit data" << G4endl;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::Finalize()
{
  if (fFinalized) {
    return;  // Already finalized, avoid double cleanup
  }
  
  try {
    if (fRootFile && fTree) {
      fRootFile->cd();
      fTree->Write();
      G4cout << "ROOT file closed with " << fTree->GetEntries() << " events" << G4endl;
      fTree = nullptr;  // Avoid double deletion
      fRootFile->Close();
      fRootFile.reset(); // Explicitly reset the unique_ptr
    }
  }
  catch (...) {
    G4cout << "Exception during ROOT file finalization, but data may have been saved" << G4endl;
  }
  
  fFinalized = true;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::BeginEvent(G4int eventID, G4double primaryEnergy)
{
  fEventID = eventID;
  fPrimaryEnergy = primaryEnergy / MeV; // Store in MeV
  ClearEventData();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::EndEvent()
{
  fNOpticalPhotons = fPhotonPosX.size();
  fNEnergyDeposits = fEdepEnergy.size();
  if (fTree) {
    fTree->Fill();
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::AddOpticalPhoton(G4double x, G4double y, G4double z,
                                  G4double dx, G4double dy, G4double dz,
                                  G4double time, const G4String& process,
                                  const G4String& parentParticle,
                                  G4int parentID, G4int trackID)
{
  fPhotonPosX.push_back(x / mm);   // Store in mm
  fPhotonPosY.push_back(y / mm);
  fPhotonPosZ.push_back(z / mm);
  fPhotonDirX.push_back(dx);
  fPhotonDirY.push_back(dy);
  fPhotonDirZ.push_back(dz);
  fPhotonTime.push_back(time / ns); // Store in ns
  fPhotonProcess.push_back(std::string(process));
  fPhotonParent.push_back(std::string(parentParticle));
  fPhotonParentID.push_back(parentID);
  fPhotonTrackID.push_back(trackID);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::AddEnergyDeposit(G4double x, G4double y, G4double z,
                                  G4double energy, G4double time,
                                  const G4String& particleName,
                                  G4int trackID, G4int parentID)
{
  fEdepPosX.push_back(x / mm);        // Store in mm
  fEdepPosY.push_back(y / mm);
  fEdepPosZ.push_back(z / mm);
  fEdepEnergy.push_back(energy / MeV); // Store in MeV
  fEdepTime.push_back(time / ns);      // Store in ns
  fEdepParticle.push_back(std::string(particleName));
  fEdepTrackID.push_back(trackID);
  fEdepParentID.push_back(parentID);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::RegisterTrack(G4int trackID, const G4String& particleName, G4int parentID)
{
  fTrackRegistry[trackID] = particleName;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4String DataManager::GetParticleNameFromTrackID(G4int trackID)
{
  auto it = fTrackRegistry.find(trackID);
  if (it != fTrackRegistry.end()) {
    return it->second;
  }
  return "Unknown";
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::ClearTrackRegistry()
{
  fTrackRegistry.clear();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::ClearEventData()
{
  fPhotonPosX.clear();
  fPhotonPosY.clear();
  fPhotonPosZ.clear();
  fPhotonDirX.clear();
  fPhotonDirY.clear();
  fPhotonDirZ.clear();
  fPhotonTime.clear();
  fPhotonProcess.clear();
  fPhotonParent.clear();
  fPhotonParentID.clear();
  fPhotonTrackID.clear();
  
  // Clear energy deposit data
  fEdepPosX.clear();
  fEdepPosY.clear();
  fEdepPosZ.clear();
  fEdepEnergy.clear();
  fEdepTime.clear();
  fEdepParticle.clear();
  fEdepTrackID.clear();
  fEdepParentID.clear();
  
  // Clear track registry for new event
  ClearTrackRegistry();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim