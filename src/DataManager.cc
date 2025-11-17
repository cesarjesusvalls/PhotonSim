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
#include "TH1D.h"
#include "G4SystemOfUnits.hh"
#include "G4ios.hh"
#include <cmath>
#include <set>

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
  fTree->Branch("PhotonWavelength", &fPhotonWavelength);
  fTree->Branch("PhotonProcess", &fPhotonProcess);
  fTree->Branch("PhotonCategory", &fPhotonCategory);
  fTree->Branch("PhotonSubCategoryID", &fPhotonSubCategoryID);
  fTree->Branch("PhotonGenealogySize", &fPhotonGenealogySize);
  fTree->Branch("PhotonGenealogyData", &fPhotonGenealogyData);

  // Event-level track information branches
  fTree->Branch("TrackInfo_TrackID", &fTrackInfo_TrackID);
  fTree->Branch("TrackInfo_Category", &fTrackInfo_Category);
  fTree->Branch("TrackInfo_SubID", &fTrackInfo_SubID);
  fTree->Branch("TrackInfo_PosX", &fTrackInfo_PosX);
  fTree->Branch("TrackInfo_PosY", &fTrackInfo_PosY);
  fTree->Branch("TrackInfo_PosZ", &fTrackInfo_PosZ);
  fTree->Branch("TrackInfo_DirX", &fTrackInfo_DirX);
  fTree->Branch("TrackInfo_DirY", &fTrackInfo_DirY);
  fTree->Branch("TrackInfo_DirZ", &fTrackInfo_DirZ);
  fTree->Branch("TrackInfo_Energy", &fTrackInfo_Energy);
  fTree->Branch("TrackInfo_Time", &fTrackInfo_Time);
  fTree->Branch("TrackInfo_ParentTrackID", &fTrackInfo_ParentTrackID);
  fTree->Branch("TrackInfo_PDG", &fTrackInfo_PDG);
  
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

  // Photon wavelength histogram: Wavelength (0-800 nm, full range)
  fPhotonHist_Wavelength = new TH1D("PhotonHist_Wavelength",
                                   "Photon Wavelength Distribution;Wavelength (nm);Counts",
                                   800, 0.0, 800.0);          // 0 to 800 nm

  G4cout << "ROOT file " << actualFilename << " created for optical photon and energy deposit data" << G4endl;
  G4cout << "2D histograms created: 500x500 bins for aggregated data analysis" << G4endl;
  G4cout << "1D wavelength histogram created: 800 bins from 0-800 nm" << G4endl;
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
      if (fPhotonHist_Wavelength) {
        fPhotonHist_Wavelength->Write();
        G4cout << "Photon wavelength histogram written with " << fPhotonHist_Wavelength->GetEntries() << " entries" << G4endl;
        // Histogram is now owned by the ROOT file, don't delete it manually
        fPhotonHist_Wavelength = nullptr;
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
  fPhotonHist_TimeDistance = nullptr;
  fPhotonHist_Wavelength = nullptr;
  
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

  // Collect track IDs to store: categorized tracks + their parents (no duplicates)
  std::set<G4int> tracksToStore;

  for (const auto& pair : fTrackRegistry) {
    const TrackInfo& info = pair.second;
    if (info.category >= 0) {
      // Store categorized tracks
      tracksToStore.insert(info.trackID);
      // Also store their parents (if they exist in registry)
      if (info.parentTrackID > 0) {
        tracksToStore.insert(info.parentTrackID);
      }
    }
  }

  // Now store all unique tracks
  for (G4int trackID : tracksToStore) {
    auto it = fTrackRegistry.find(trackID);
    if (it != fTrackRegistry.end()) {
      const TrackInfo& info = it->second;
      fTrackInfo_TrackID.push_back(info.trackID);
      fTrackInfo_Category.push_back(info.category);  // May be -1 for non-categorized parents
      fTrackInfo_SubID.push_back(info.subID);        // May be -1 for non-categorized parents
      fTrackInfo_PosX.push_back(info.posX / mm);
      fTrackInfo_PosY.push_back(info.posY / mm);
      fTrackInfo_PosZ.push_back(info.posZ / mm);
      fTrackInfo_DirX.push_back(info.dirX);
      fTrackInfo_DirY.push_back(info.dirY);
      fTrackInfo_DirZ.push_back(info.dirZ);
      fTrackInfo_Energy.push_back(info.energy / MeV);
      fTrackInfo_Time.push_back(info.time / ns);
      fTrackInfo_ParentTrackID.push_back(info.parentTrackID);
      fTrackInfo_PDG.push_back(info.pdgCode);
    }
  }

  if (fTree) {
    fTree->Fill();
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::AddOpticalPhoton(G4double x, G4double y, G4double z,
                                  G4double dx, G4double dy, G4double dz,
                                  G4double time, G4double wavelength,
                                  const G4String& process,
                                  G4int category,
                                  G4int subID,
                                  const std::vector<G4int>& genealogy)
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

  // Fill wavelength histogram
  if (fPhotonHist_Wavelength) {
    G4double wavelength_nm = wavelength / nm;  // Convert to nm
    fPhotonHist_Wavelength->Fill(wavelength_nm);
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
    fPhotonWavelength.push_back(wavelength / nm); // Store in nm
    fPhotonProcess.push_back(std::string(process));
    fPhotonCategory.push_back(category);
    fPhotonSubCategoryID.push_back(subID);

    // Store flattened genealogy
    fPhotonGenealogySize.push_back(genealogy.size());
    for (const auto& trackID : genealogy) {
      fPhotonGenealogyData.push_back(trackID);
    }
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

void DataManager::RegisterTrack(G4int trackID, const G4String& particleName, G4int parentID,
                               const G4ThreeVector& position, const G4ThreeVector& momentum,
                               G4double energy, G4double time, G4int pdgCode)
{
  TrackInfo info;
  info.trackID = trackID;
  info.category = -1;  // Not yet categorized
  info.subID = -1;
  info.posX = position.x();
  info.posY = position.y();
  info.posZ = position.z();
  info.dirX = momentum.unit().x();
  info.dirY = momentum.unit().y();
  info.dirZ = momentum.unit().z();
  info.energy = energy;
  info.time = time;
  info.parentTrackID = parentID;
  info.particleName = particleName;
  info.pdgCode = pdgCode;
  info.preMomentumDir = momentum.unit();  // Store initial momentum

  fTrackRegistry[trackID] = info;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::UpdateTrackCategory(G4int trackID, G4int category, G4int subID, G4int categoryParentTrackID)
{
  auto it = fTrackRegistry.find(trackID);
  if (it != fTrackRegistry.end()) {
    it->second.category = category;
    it->second.subID = subID;
    it->second.parentTrackID = categoryParentTrackID;
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::UpdatePionMomentum(G4int trackID, const G4ThreeVector& momentum)
{
  auto it = fTrackRegistry.find(trackID);
  if (it != fTrackRegistry.end()) {
    it->second.preMomentumDir = momentum.unit();
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

TrackInfo* DataManager::GetTrackInfo(G4int trackID)
{
  auto it = fTrackRegistry.find(trackID);
  if (it != fTrackRegistry.end()) {
    return &(it->second);
  }
  return nullptr;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

std::vector<G4int> DataManager::BuildGenealogy(G4int trackID)
{
  std::vector<G4int> genealogy;

  TrackInfo* info = GetTrackInfo(trackID);
  if (!info) return genealogy;

  // Build ancestry chain by following parent track IDs
  // Only include tracks that have been assigned a category
  G4int currentTrackID = trackID;
  while (currentTrackID > 0) {
    TrackInfo* currentInfo = GetTrackInfo(currentTrackID);
    if (!currentInfo) break;

    // Only add to genealogy if this track has a category assigned
    if (currentInfo->category >= 0) {
      genealogy.insert(genealogy.begin(), currentTrackID);  // Insert at front to maintain order
    }

    currentTrackID = currentInfo->parentTrackID;
  }

  return genealogy;
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
  fPhotonWavelength.clear();
  fPhotonProcess.clear();
  fPhotonCategory.clear();
  fPhotonSubCategoryID.clear();
  fPhotonGenealogySize.clear();
  fPhotonGenealogyData.clear();

  // Clear energy deposit data
  fEdepPosX.clear();
  fEdepPosY.clear();
  fEdepPosZ.clear();
  fEdepEnergy.clear();
  fEdepTime.clear();
  fEdepParticle.clear();
  fEdepTrackID.clear();
  fEdepParentID.clear();

  // Clear track info arrays
  fTrackInfo_TrackID.clear();
  fTrackInfo_Category.clear();
  fTrackInfo_SubID.clear();
  fTrackInfo_PosX.clear();
  fTrackInfo_PosY.clear();
  fTrackInfo_PosZ.clear();
  fTrackInfo_DirX.clear();
  fTrackInfo_DirY.clear();
  fTrackInfo_DirZ.clear();
  fTrackInfo_Energy.clear();
  fTrackInfo_Time.clear();
  fTrackInfo_ParentTrackID.clear();
  fTrackInfo_PDG.clear();

  // Reset category counters
  fNDecayElectrons = 0;
  fNSecondaryPions = 0;
  fNGammaShowers = 0;

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
  fPhotonHist_TimeDistance = nullptr;
  fPhotonHist_Wavelength = nullptr;
  fTree = nullptr;
  fRootFile.reset();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim