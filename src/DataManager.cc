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
#include <algorithm>

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
  fTree->Branch("PhotonPolX", &fPhotonPolX);
  fTree->Branch("PhotonPolY", &fPhotonPolY);
  fTree->Branch("PhotonPolZ", &fPhotonPolZ);
  fTree->Branch("PhotonProcess", &fPhotonProcess);

  // Particle system branches (categorized particles based on genealogy)
  fTree->Branch("NParticles", &fNParticles, "NParticles/I");
  fTree->Branch("Particle_GenealogySize", &fParticle_GenealogySize);
  fTree->Branch("Particle_GenealogyData", &fParticle_GenealogyData);
  fTree->Branch("Particle_PhotonIDsSize", &fParticle_PhotonIDsSize);
  fTree->Branch("Particle_PhotonIDsData", &fParticle_PhotonIDsData);
  fTree->Branch("Particle_ExtGenealogySize", &fParticle_ExtGenealogySize);
  fTree->Branch("Particle_ExtGenealogyData", &fParticle_ExtGenealogyData);

  // Meaningful tracks table (tracks contributing to Cherenkov emission)
  fTree->Branch("NMeaningfulTracks", &fNMeaningfulTracks, "NMeaningfulTracks/I");
  fTree->Branch("MTrack_TrackID", &fMTrack_TrackID);
  fTree->Branch("MTrack_ParentID", &fMTrack_ParentID);
  fTree->Branch("MTrack_PDG", &fMTrack_PDG);
  fTree->Branch("MTrack_InitialEnergy", &fMTrack_InitialEnergy);
  fTree->Branch("MTrack_ParticleName", &fMTrack_ParticleName);
  fTree->Branch("MTrack_NCherenkov", &fMTrack_NCherenkov);
  fTree->Branch("MTrack_SegmentOffset", &fMTrack_SegmentOffset);
  fTree->Branch("MTrack_NSegments", &fMTrack_NSegments);

  // Segments table (all steps for meaningful tracks)
  fTree->Branch("NSegments", &fNSegments, "NSegments/I");
  fTree->Branch("Segment_StartX", &fSegment_StartX);
  fTree->Branch("Segment_StartY", &fSegment_StartY);
  fTree->Branch("Segment_StartZ", &fSegment_StartZ);
  fTree->Branch("Segment_EndX", &fSegment_EndX);
  fTree->Branch("Segment_EndY", &fSegment_EndY);
  fTree->Branch("Segment_EndZ", &fSegment_EndZ);
  fTree->Branch("Segment_DirX", &fSegment_DirX);
  fTree->Branch("Segment_DirY", &fSegment_DirY);
  fTree->Branch("Segment_DirZ", &fSegment_DirZ);
  fTree->Branch("Segment_Edep", &fSegment_Edep);
  fTree->Branch("Segment_Time", &fSegment_Time);

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
  
  // dE/dx histogram: dE/dx (0-1000 keV/mm) vs Distance (0-10 m)
  // Format matches PhotonHist_AngleDistance: X-axis is the observable, Y-axis is distance
  fdEdxHist_Distance = new TH2D("dEdxHist_Distance",
                                "dE/dx vs Distance from Origin;dE/dx (keV/mm);Distance (mm)",
                                500, 0.0, 1000.0,           // 0 to 1000 keV/mm
                                500, 0.0, 10000.0);         // 0 to 10 meters in mm
  
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
      if (fdEdxHist_Distance) {
        fdEdxHist_Distance->Write();
        G4cout << "dE/dx histogram written with " << fdEdxHist_Distance->GetEntries() << " entries" << G4endl;
        // Histogram is now owned by the ROOT file, don't delete it manually
        fdEdxHist_Distance = nullptr;
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
  fdEdxHist_Distance = nullptr;
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

  // Skip track segment processing when individual photon storage is disabled
  // (used for lookup table generation where only histograms are needed)
  if (!fStoreIndividualPhotons) {
    if (fTree) {
      fTree->Fill();
    }
    return;
  }

  // === Step 1: Identify meaningful tracks ===
  // A track is meaningful if it produced Cherenkov photons OR has a descendant that did
  std::set<G4int> meaningfulTrackIDs;

  // First pass: find all tracks that directly produced Cherenkov photons
  for (const auto& pair : fAllTrackSegments) {
    if (pair.second.cherenkovCount > 0) {
      meaningfulTrackIDs.insert(pair.first);
    }
  }

  // Second pass: walk up ancestry to mark all ancestors as meaningful
  std::set<G4int> ancestorsToAdd;
  for (G4int trackID : meaningfulTrackIDs) {
    G4int currentID = trackID;
    while (currentID > 0) {
      auto it = fAllTrackSegments.find(currentID);
      if (it == fAllTrackSegments.end()) break;
      ancestorsToAdd.insert(currentID);
      currentID = it->second.parentID;
    }
  }
  meaningfulTrackIDs.insert(ancestorsToAdd.begin(), ancestorsToAdd.end());

  // === Step 2: Output meaningful tracks and their merged segments ===
  // Merging criteria:
  //   - For tracks >= 10 MeV: minimum 10mm length OR direction change > 2 degrees
  //   - For tracks < 10 MeV: merge until energy loss >= 1 MeV (regardless of length/angle)
  const G4double minSegmentLength = 10.0;  // mm
  const G4double maxAngleForMerge = 2.0 * M_PI / 180.0;  // 2 degrees in radians
  const G4double lowEnergyThreshold = 10.0;  // MeV - tracks below this use edep-based merging
  const G4double minEdepForLowEnergy = 1.0;  // MeV - minimum edep before saving segment for low-E tracks

  fNMeaningfulTracks = meaningfulTrackIDs.size();
  G4int segmentOffset = 0;

  for (G4int trackID : meaningfulTrackIDs) {
    auto it = fAllTrackSegments.find(trackID);
    if (it == fAllTrackSegments.end()) continue;

    const TrackSegmentInfo& info = it->second;
    bool isLowEnergy = (info.initialEnergy / MeV) < lowEnergyThreshold;

    // Merge segments for this track
    std::vector<TrackSegment> mergedSegments;

    if (!info.segments.empty()) {
      TrackSegment current = info.segments[0];

      for (size_t i = 1; i < info.segments.size(); i++) {
        const TrackSegment& next = info.segments[i];

        bool shouldSave = false;

        if (isLowEnergy) {
          // Low energy track: merge until edep >= 1 MeV
          shouldSave = (current.edep >= minEdepForLowEnergy);
        } else {
          // Normal track: use length and angle criteria
          // Calculate current merged segment length
          G4double dx = current.endX - current.startX;
          G4double dy = current.endY - current.startY;
          G4double dz = current.endZ - current.startZ;
          G4double currentLength = std::sqrt(dx*dx + dy*dy + dz*dz);

          // Calculate direction change (angle between current direction and next direction)
          G4double dot = current.dirX * next.dirX + current.dirY * next.dirY + current.dirZ * next.dirZ;
          dot = std::max(-1.0, std::min(1.0, dot));  // Clamp for numerical stability
          G4double angle = std::acos(dot);

          bool significantDeflection = (angle > maxAngleForMerge);
          bool reachedMinLength = (currentLength >= minSegmentLength);
          shouldSave = (significantDeflection || reachedMinLength);
        }

        if (shouldSave) {
          // Save current merged segment
          mergedSegments.push_back(current);
          // Start new segment
          current = next;
        } else {
          // Merge: extend end position, accumulate edep, keep original start and direction
          current.endX = next.endX;
          current.endY = next.endY;
          current.endZ = next.endZ;
          current.edep += next.edep;
        }
      }
      // Don't forget the last segment
      mergedSegments.push_back(current);
    }

    fMTrack_TrackID.push_back(info.trackID);
    fMTrack_ParentID.push_back(info.parentID);
    fMTrack_PDG.push_back(info.pdgCode);
    fMTrack_InitialEnergy.push_back(info.initialEnergy / MeV);
    fMTrack_ParticleName.push_back(std::string(info.particleName));
    fMTrack_NCherenkov.push_back(info.cherenkovCount);
    fMTrack_SegmentOffset.push_back(segmentOffset);
    fMTrack_NSegments.push_back(mergedSegments.size());

    // Output merged segments for this track
    for (const TrackSegment& seg : mergedSegments) {
      fSegment_StartX.push_back(seg.startX);
      fSegment_StartY.push_back(seg.startY);
      fSegment_StartZ.push_back(seg.startZ);
      fSegment_EndX.push_back(seg.endX);
      fSegment_EndY.push_back(seg.endY);
      fSegment_EndZ.push_back(seg.endZ);
      fSegment_DirX.push_back(seg.dirX);
      fSegment_DirY.push_back(seg.dirY);
      fSegment_DirZ.push_back(seg.dirZ);
      fSegment_Edep.push_back(seg.edep);
      fSegment_Time.push_back(seg.time);
    }

    segmentOffset += mergedSegments.size();
  }
  fNSegments = segmentOffset;

  // === Step 3: Convert genealogy map to particle arrays with extended genealogy ===
  fNParticles = fGenealogyToPhotonIDs.size();

  for (const auto& pair : fGenealogyToPhotonIDs) {
    const std::vector<G4int>& genealogy = pair.first;
    const std::vector<G4int>& photonIDs = pair.second;

    // Store genealogy (categorized track IDs only)
    fParticle_GenealogySize.push_back(genealogy.size());
    for (G4int trackID : genealogy) {
      fParticle_GenealogyData.push_back(trackID);
    }

    // Store photon IDs for this particle
    fParticle_PhotonIDsSize.push_back(photonIDs.size());
    for (G4int photonID : photonIDs) {
      fParticle_PhotonIDsData.push_back(photonID);
    }

    // Build and store extended genealogy (all meaningful track IDs in ancestry)
    // Use the last track in genealogy as the starting point
    std::set<G4int> extGenealogySet;
    if (!genealogy.empty()) {
      G4int leafTrackID = genealogy.back();
      std::vector<G4int> extGen = BuildExtendedGenealogy(leafTrackID);
      // Filter to only include meaningful tracks
      for (G4int tid : extGen) {
        if (meaningfulTrackIDs.count(tid) > 0) {
          extGenealogySet.insert(tid);
        }
      }
    }
    // Convert set to vector maintaining order
    std::vector<G4int> extGenealogyVec(extGenealogySet.begin(), extGenealogySet.end());
    std::sort(extGenealogyVec.begin(), extGenealogyVec.end());

    fParticle_ExtGenealogySize.push_back(extGenealogyVec.size());
    for (G4int tid : extGenealogyVec) {
      fParticle_ExtGenealogyData.push_back(tid);
    }
  }

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
                                  G4double polX, G4double polY, G4double polZ,
                                  const G4String& process,
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
    fPhotonPolX.push_back(polX);     // Store polarization (unit vector)
    fPhotonPolY.push_back(polY);
    fPhotonPolZ.push_back(polZ);
    fPhotonProcess.push_back(std::string(process));

    // Track this photon's genealogy (photon index is current size - 1)
    G4int photonIndex = fPhotonPosX.size() - 1;
    fGenealogyToPhotonIDs[genealogy].push_back(photonIndex);
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::AddEnergyDeposit(G4double x, G4double y, G4double z,
                                  G4double energy, G4double stepLength,
                                  G4double time,
                                  const G4String& particleName,
                                  G4int trackID, G4int parentID)
{
  // Fill the dE/dx histogram for aggregated data
  // Skip photons (gamma and opticalphoton) - dE/dx is not meaningful for them
  if (fdEdxHist_Distance && particleName != "gamma" && particleName != "opticalphoton") {
    // Only fill if step length is positive to avoid division by zero
    if (stepLength > 0.0) {
      // Calculate distance from origin
      G4double distance = std::sqrt(x*x + y*y + z*z) / mm;  // Convert to mm

      // Calculate dE/dx in keV/mm
      G4double stepLength_mm = stepLength / mm;
      G4double dEdx = (energy / keV) / stepLength_mm;

      // Fill histogram: X-axis is dE/dx, Y-axis is distance
      fdEdxHist_Distance->Fill(dEdx, distance);
    }
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

void DataManager::UpdatePionMomentum(G4int trackID, const G4ThreeVector& momentumDir,
                                     const G4ThreeVector& position, G4double time)
{
  auto it = fTrackRegistry.find(trackID);
  if (it != fTrackRegistry.end()) {
    // Store momentum direction, position, and time as synchronized triplet
    it->second.preMomentumDir = momentumDir.unit();
    it->second.preMomentumPos = position;
    it->second.preMomentumTime = time;
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

void DataManager::AddTrackSegment(G4int trackID, G4int parentID, G4int pdgCode,
                                  const G4String& particleName, G4double initialEnergy,
                                  G4double startX, G4double startY, G4double startZ,
                                  G4double endX, G4double endY, G4double endZ,
                                  G4double dirX, G4double dirY, G4double dirZ,
                                  G4double edep, G4double time)
{
  // Get or create track segment info
  auto it = fAllTrackSegments.find(trackID);
  if (it == fAllTrackSegments.end()) {
    // First segment for this track - create entry
    TrackSegmentInfo info;
    info.trackID = trackID;
    info.parentID = parentID;
    info.pdgCode = pdgCode;
    info.particleName = particleName;
    info.initialEnergy = initialEnergy;
    info.cherenkovCount = 0;
    fAllTrackSegments[trackID] = info;
    it = fAllTrackSegments.find(trackID);
  }

  // Add segment
  TrackSegment seg;
  seg.startX = startX / mm;
  seg.startY = startY / mm;
  seg.startZ = startZ / mm;
  seg.endX = endX / mm;
  seg.endY = endY / mm;
  seg.endZ = endZ / mm;
  seg.dirX = dirX;
  seg.dirY = dirY;
  seg.dirZ = dirZ;
  seg.edep = edep / MeV;
  seg.time = time / ns;

  it->second.segments.push_back(seg);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::IncrementCherenkovCount(G4int trackID)
{
  auto it = fAllTrackSegments.find(trackID);
  if (it != fAllTrackSegments.end()) {
    it->second.cherenkovCount++;
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

std::vector<G4int> DataManager::BuildExtendedGenealogy(G4int trackID)
{
  std::vector<G4int> extGenealogy;

  // Walk up the ancestry using fAllTrackSegments (which has parent info)
  G4int currentTrackID = trackID;
  while (currentTrackID > 0) {
    auto it = fAllTrackSegments.find(currentTrackID);
    if (it == fAllTrackSegments.end()) break;

    // Add this track to the genealogy (at front to maintain root->leaf order)
    extGenealogy.insert(extGenealogy.begin(), currentTrackID);

    // Move to parent
    currentTrackID = it->second.parentID;
  }

  return extGenealogy;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::RelabelPhotonsForDeflection(G4int newTrackID, G4int oldTrackID, G4double deflectionTime)
{
  // Build the new genealogy for the deflected track
  std::vector<G4int> newGenealogy = BuildGenealogy(newTrackID);

  // Build the old genealogy (parent track's genealogy)
  std::vector<G4int> oldGenealogy = BuildGenealogy(oldTrackID);

  // Find photons in the old genealogy that were created after deflection time
  auto it = fGenealogyToPhotonIDs.find(oldGenealogy);
  if (it == fGenealogyToPhotonIDs.end()) {
    return; // No photons with this genealogy
  }

  std::vector<G4int>& oldPhotonIDs = it->second;
  std::vector<G4int> photonsToMove;

  // Find photons created at or after deflection time
  for (G4int photonID : oldPhotonIDs) {
    if (photonID >= 0 && photonID < static_cast<G4int>(fPhotonTime.size())) {
      G4double photonTime = fPhotonTime[photonID] * ns; // Convert back to GEANT4 units
      if (photonTime >= deflectionTime) {
        photonsToMove.push_back(photonID);
      }
    }
  }

  if (photonsToMove.empty()) {
    return; // No photons to relabel
  }

  // Remove moved photons from old genealogy
  for (G4int photonID : photonsToMove) {
    oldPhotonIDs.erase(std::remove(oldPhotonIDs.begin(), oldPhotonIDs.end(), photonID), oldPhotonIDs.end());
  }

  // Add photons to new genealogy
  std::vector<G4int>& newPhotonIDs = fGenealogyToPhotonIDs[newGenealogy];
  newPhotonIDs.insert(newPhotonIDs.end(), photonsToMove.begin(), photonsToMove.end());

  G4cout << "      >>> Relabeled " << photonsToMove.size() << " photons from genealogy ending with "
         << oldTrackID << " to genealogy ending with " << newTrackID << G4endl;
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
  fPhotonPolX.clear();
  fPhotonPolY.clear();
  fPhotonPolZ.clear();
  fPhotonProcess.clear();

  // Clear particle system
  fNParticles = 0;
  fParticle_GenealogySize.clear();
  fParticle_GenealogyData.clear();
  fParticle_PhotonIDsSize.clear();
  fParticle_PhotonIDsData.clear();
  fParticle_ExtGenealogySize.clear();
  fParticle_ExtGenealogyData.clear();
  fGenealogyToPhotonIDs.clear();

  // Clear temporary track segment storage
  fAllTrackSegments.clear();

  // Clear meaningful tracks output
  fNMeaningfulTracks = 0;
  fMTrack_TrackID.clear();
  fMTrack_ParentID.clear();
  fMTrack_PDG.clear();
  fMTrack_InitialEnergy.clear();
  fMTrack_ParticleName.clear();
  fMTrack_NCherenkov.clear();
  fMTrack_SegmentOffset.clear();
  fMTrack_NSegments.clear();

  // Clear segments output
  fNSegments = 0;
  fSegment_StartX.clear();
  fSegment_StartY.clear();
  fSegment_StartZ.clear();
  fSegment_EndX.clear();
  fSegment_EndY.clear();
  fSegment_EndZ.clear();
  fSegment_DirX.clear();
  fSegment_DirY.clear();
  fSegment_DirZ.clear();
  fSegment_Edep.clear();
  fSegment_Time.clear();

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
  fNPrimaries = 0;
  fNDecayElectrons = 0;
  fNSecondaryPions = 0;
  fNGammas = 0;

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
  fdEdxHist_Distance = nullptr;
  fPhotonHist_TimeDistance = nullptr;
  fPhotonHist_Wavelength = nullptr;
  fTree = nullptr;
  fRootFile.reset();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::PrintPionSummary(G4int eventID)
{
  G4cout << "\n";
  G4cout << "╔════════════════════════════════════════════════════════════════╗" << G4endl;
  G4cout << "║          PION SUMMARY FOR EVENT " << eventID << "                          ║" << G4endl;
  G4cout << "╚════════════════════════════════════════════════════════════════╝" << G4endl;

  // Count pions by category
  G4int primaryPions = 0;
  G4int secondaryPions = 0;
  G4int uncategorizedPions = 0;

  // Store pion track IDs for detailed printout
  std::vector<G4int> primaryIDs, secondaryIDs, uncategorizedIDs;

  for (const auto& entry : fTrackRegistry) {
    const TrackInfo& info = entry.second;
    if (info.particleName == "pi+" || info.particleName == "pi-") {
      if (info.category == kPrimary) {
        primaryPions++;
        primaryIDs.push_back(info.trackID);
      } else if (info.category == kSecondaryPion) {
        secondaryPions++;
        secondaryIDs.push_back(info.trackID);
      } else {
        uncategorizedPions++;
        uncategorizedIDs.push_back(info.trackID);
      }
    }
  }

  G4cout << "\nCATEGORY COUNTS:" << G4endl;
  G4cout << "  Primary pions:       " << primaryPions << G4endl;
  G4cout << "  Secondary pions:     " << secondaryPions << G4endl;
  G4cout << "  Uncategorized pions: " << uncategorizedPions << G4endl;
  G4cout << "  TOTAL pions:         " << (primaryPions + secondaryPions + uncategorizedPions) << G4endl;

  if (uncategorizedPions > 0) {
    G4cout << "\n⚠ WARNING: Found " << uncategorizedPions << " uncategorized pion(s)!" << G4endl;
    G4cout << "\nUNCATEGORIZED PION DETAILS:" << G4endl;
    for (G4int trackID : uncategorizedIDs) {
      const TrackInfo& info = fTrackRegistry[trackID];
      G4cout << "  ─────────────────────────────────────────" << G4endl;
      G4cout << "  TrackID: " << trackID << G4endl;
      G4cout << "  Particle: " << info.particleName << " (PDG: " << info.pdgCode << ")" << G4endl;
      G4cout << "  ParentID: " << info.parentTrackID << G4endl;

      TrackInfo* parentInfo = GetTrackInfo(info.parentTrackID);
      if (parentInfo) {
        G4cout << "  Parent: " << parentInfo->particleName
               << " (category=" << parentInfo->category << ")" << G4endl;
      }

      G4cout << "  Energy: " << info.energy << " MeV" << G4endl;
      G4cout << "  Position: (" << info.posX << ", " << info.posY << ", " << info.posZ << ")" << G4endl;
    }
  }

  if (secondaryPions > 0) {
    G4cout << "\nSECONDARY PION DETAILS:" << G4endl;
    for (G4int trackID : secondaryIDs) {
      const TrackInfo& info = fTrackRegistry[trackID];
      G4cout << "  ─────────────────────────────────────────" << G4endl;
      G4cout << "  TrackID: " << trackID << " (subID: " << info.subID << ")" << G4endl;
      G4cout << "  Particle: " << info.particleName << G4endl;
      G4cout << "  ParentID: " << info.parentTrackID << G4endl;

      TrackInfo* parentInfo = GetTrackInfo(info.parentTrackID);
      if (parentInfo) {
        G4cout << "  Parent: " << parentInfo->particleName
               << " (category=" << parentInfo->category << ")" << G4endl;
      }

      G4cout << "  Energy: " << info.energy << " MeV" << G4endl;
    }
  }

  G4cout << "\n════════════════════════════════════════════════════════════════\n" << G4endl;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim