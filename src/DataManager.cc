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
#include "TH2D.h"
#include "G4SystemOfUnits.hh"
#include "G4ios.hh"
#include <cmath>

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

void DataManager::DeleteInstance()
{
  if (fInstance) {
    delete fInstance;
    fInstance = nullptr;
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::Initialize(const G4String& filename)
{
  // Use provided filename, or stored filename if none provided
  G4String actualFilename = filename.empty() ? fOutputFilename : filename;
  
  fRootFile = std::make_unique<TFile>(actualFilename.c_str(), "RECREATE");
  if (!fRootFile || fRootFile->IsZombie()) {
    G4cerr << "Error: Cannot create ROOT file " << actualFilename << G4endl;
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
  
  // Create 2D histograms for aggregated data (500x500 bins)
  // Photon histogram: Opening angle (0-π rad) vs Distance (0-10 m)
  fPhotonHist_AngleDistance = new TH2D("PhotonHist_AngleDistance", 
                                      "Photon Opening Angle vs Distance from Origin;Opening Angle (rad);Distance (mm)",
                                      500, 0.0, M_PI,           // 0 to π radians (all possible angles)
                                      500, 0.0, 10000.0);       // 0 to 10 meters in mm
  
  // Energy deposit histogram: Distance (0-10 m) vs Energy (0-? keV, to be determined)
  // Start with 0-1000 keV range, can be adjusted based on data
  fEdepHist_DistanceEnergy = new TH2D("EdepHist_DistanceEnergy",
                                     "Energy Deposit vs Distance from Origin;Distance (mm);Energy Deposit (keV)",
                                     500, 0.0, 10000.0,        // 0 to 10 meters in mm
                                     500, 0.0, 1000.0);        // 0 to 1000 keV (adjustable)
  
  // Photon time vs distance histogram: Distance (0-10 m) vs Time (0-50 ns)
  fPhotonHist_TimeDistance = new TH2D("PhotonHist_TimeDistance",
                                     "Photon Time vs Distance from Origin;Distance (mm);Time (ns)",
                                     500, 0.0, 10000.0,        // 0 to 10 meters in mm
                                     500, 0.0, 50.0);          // 0 to 50 ns
  
  G4cout << "ROOT file " << actualFilename << " created for optical photon and energy deposit data" << G4endl;
  G4cout << "2D histograms created: 500x500 bins for aggregated data analysis" << G4endl;
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
      
      // Write histograms
      if (fPhotonHist_AngleDistance) {
        fPhotonHist_AngleDistance->Write();
        G4cout << "Photon histogram written with " << fPhotonHist_AngleDistance->GetEntries() << " entries" << G4endl;
        // Histogram is now owned by the ROOT file, don't delete it manually
        fPhotonHist_AngleDistance = nullptr;
      }
      if (fEdepHist_DistanceEnergy) {
        fEdepHist_DistanceEnergy->Write();
        G4cout << "Energy deposit histogram written with " << fEdepHist_DistanceEnergy->GetEntries() << " entries" << G4endl;
        // Histogram is now owned by the ROOT file, don't delete it manually
        fEdepHist_DistanceEnergy = nullptr;
      }
      if (fPhotonHist_TimeDistance) {
        fPhotonHist_TimeDistance->Write();
        G4cout << "Photon time histogram written with " << fPhotonHist_TimeDistance->GetEntries() << " entries" << G4endl;
        // Histogram is now owned by the ROOT file, don't delete it manually
        fPhotonHist_TimeDistance = nullptr;
      }
      
      G4cout << "ROOT file closed with " << fTree->GetEntries() << " events" << G4endl;
      
      // Important: Let ROOT manage the tree cleanup when the file is closed
      fTree = nullptr;  // Tree will be deleted by ROOT file
      
      // Close and reset the file
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

void DataManager::Reset()
{
  // Finalize any existing file first
  if (!fFinalized) {
    Finalize();
  }
  
  // Reset all state
  fFinalized = false;
  fTree = nullptr;
  fRootFile.reset();
  fPhotonHist_AngleDistance = nullptr;
  fEdepHist_DistanceEnergy = nullptr;
  
  // Clear output filename
  fOutputFilename = "output.root";
  
  // Reset storage flags
  fStoreIndividualPhotons = false;
  fStoreIndividualEdeps = false;
  
  // Clear all data
  ClearEventData();
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
  // Always fill the 2D histogram for aggregated data
  if (fPhotonHist_AngleDistance) {
    // Calculate distance from origin
    G4double distance = std::sqrt(x*x + y*y + z*z) / mm;  // Convert to mm
    
    // Calculate opening angle with respect to muon direction (0,0,1)
    // Assume muon travels along +Z axis
    G4double muon_z = 1.0;  // Unit vector in Z direction
    G4double dot_product = dz * muon_z;  // dx*0 + dy*0 + dz*1 = dz
    G4double opening_angle = std::acos(std::max(-1.0, std::min(1.0, dot_product)));
    
    fPhotonHist_AngleDistance->Fill(opening_angle, distance);
    
    // Fill time vs distance histogram
    G4double time_ns = time / ns;  // Convert to ns
    fPhotonHist_TimeDistance->Fill(distance, time_ns);
  }
  
  // Conditionally store individual photon data
  if (fStoreIndividualPhotons) {
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
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::AddEnergyDeposit(G4double x, G4double y, G4double z,
                                  G4double energy, G4double time,
                                  const G4String& particleName,
                                  G4int trackID, G4int parentID)
{
  // Always fill the 2D histogram for aggregated data
  if (fEdepHist_DistanceEnergy) {
    // Calculate distance from origin
    G4double distance = std::sqrt(x*x + y*y + z*z) / mm;  // Convert to mm
    
    // Convert energy to keV for histogram
    G4double energy_keV = energy / keV;
    
    fEdepHist_DistanceEnergy->Fill(distance, energy_keV);
  }
  
  // Conditionally store individual energy deposit data
  if (fStoreIndividualEdeps) {
    fEdepPosX.push_back(x / mm);        // Store in mm
    fEdepPosY.push_back(y / mm);
    fEdepPosZ.push_back(z / mm);
    fEdepEnergy.push_back(energy / MeV); // Store in MeV
    fEdepTime.push_back(time / ns);      // Store in ns
    fEdepParticle.push_back(std::string(particleName));
    fEdepTrackID.push_back(trackID);
    fEdepParentID.push_back(parentID);
  }
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

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

DataManager::~DataManager()
{
  // Make sure to finalize before destruction
  if (!fFinalized) {
    try {
      Finalize();
    } catch (...) {
      // Suppress exceptions in destructor
    }
  }
  
  // Clean up ROOT objects - histograms are already handled by Finalize()
  // Just make sure pointers are null
  fPhotonHist_AngleDistance = nullptr;
  fEdepHist_DistanceEnergy = nullptr;
  fTree = nullptr;
  fRootFile.reset();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim