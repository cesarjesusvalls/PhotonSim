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

  // GENIE provenance: -1 / 0 / 0.0 for particle-gun events. LUCiD v5
  // reads these to populate per_interaction/neutrino_pdg and
  // per_interaction/neutrino_energy_MeV.
  fTree->Branch("RooTrackerEntryID", &fGenieEntryID, "RooTrackerEntryID/I");
  fTree->Branch("IncomingNuPdg", &fIncomingNuPdg, "IncomingNuPdg/I");
  fTree->Branch("IncomingNuKE", &fIncomingNuKE, "IncomingNuKE/D");

  // Per-photon scalar measurements live on the sister tree
  // OpticalPhotonsRaw (set up below). Photon_SegmentIndex stays event-grain
  // on this metadata tree because it's derived data computed at EndEvent
  // (one int per photon, not a bulk array).
  fTree->Branch("Photon_SegmentIndex", &fPhoton_SegmentIndex);

  // Segments table — one row per G4 step of every non-optical-photon
  // track. Track ownership is inline via Segment_TrackID; LUCiD's
  // `derive_meaningful_tracks` filters Cherenkov-producing tracks via
  // groupby on this branch.
  fTree->Branch("NSegments", &fNSegments, "NSegments/I");
  fTree->Branch("Segment_TrackID", &fSegment_TrackID);
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
  fTree->Branch("Segment_BetaStart", &fSegment_BetaStart);
  fTree->Branch("Segment_NCherenkov", &fSegment_NCherenkov);

  // Event-level track information branches (one row per registered G4 track,
  // optical photons excluded at registration time).
  fTree->Branch("TrackInfo_TrackID", &fTrackInfo_TrackID);
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
  fTree->Branch("TrackInfo_CreatorProcess", &fTrackInfo_CreatorProcess);

  // === Sister tree: chunked per-photon measurements ===
  // Each entry holds up to fPhotonChunkSize photons. EventID and
  // ChunkStartID let readers locate the photons that belong to a given
  // event / global photon-id range. Memory bound: when streaming is on
  // (fStreamPhotonsChunked=true), the streamed std::vectors flush every
  // fPhotonChunkSize photons, so peak photon-vector RAM is O(K).
  fRawTree = new TTree("OpticalPhotonsRaw", "Per-photon scalars (chunked)");
  fRawTree->Branch("EventID", &fEventIDChunk, "EventID/I");
  fRawTree->Branch("ChunkStartID", &fChunkStartID, "ChunkStartID/L");
  fRawTree->Branch("PhotonPosX", &fChunk_PosX);
  fRawTree->Branch("PhotonPosY", &fChunk_PosY);
  fRawTree->Branch("PhotonPosZ", &fChunk_PosZ);
  fRawTree->Branch("PhotonDirX", &fChunk_DirX);
  fRawTree->Branch("PhotonDirY", &fChunk_DirY);
  fRawTree->Branch("PhotonDirZ", &fChunk_DirZ);
  fRawTree->Branch("PhotonTime", &fChunk_Time);
  fRawTree->Branch("PhotonWavelength", &fChunk_Wavelength);
  fRawTree->Branch("PhotonPolX", &fChunk_PolX);
  fRawTree->Branch("PhotonPolY", &fChunk_PolY);
  fRawTree->Branch("PhotonPolZ", &fChunk_PolZ);
  if (fStoreProcessName) {
    fRawTree->Branch("PhotonProcess", &fChunk_Process);
  }
  // Cap basket buffering so default behaviour doesn't accumulate many
  // chunks before flushing to disk (which would partially defeat the
  // streaming bound). 50 MB target tree-wide.
  fRawTree->SetAutoFlush(-50000000LL);

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

  G4cout << "ROOT file " << actualFilename << " created for optical photon data" << G4endl;
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
      if (fRawTree) {
        fRawTree->Write();
        G4cout << "OpticalPhotonsRaw written with " << fRawTree->GetEntries()
               << " chunk entries" << G4endl;
        fRawTree = nullptr;  // Tree owned by ROOT file after Write
      }

      // Write histograms
      if (fPhotonHist_AngleDistance) {
        fPhotonHist_AngleDistance->Write();
        G4cout << "Photon histogram written with " << fPhotonHist_AngleDistance->GetEntries() << " entries" << G4endl;
        fPhotonHist_AngleDistance = nullptr;
      }
      if (fdEdxHist_Distance) {
        fdEdxHist_Distance->Write();
        G4cout << "dE/dx histogram written with " << fdEdxHist_Distance->GetEntries() << " entries" << G4endl;
        fdEdxHist_Distance = nullptr;
      }
      if (fPhotonHist_TimeDistance) {
        fPhotonHist_TimeDistance->Write();
        G4cout << "Photon time histogram written with " << fPhotonHist_TimeDistance->GetEntries() << " entries" << G4endl;
        fPhotonHist_TimeDistance = nullptr;
      }
      if (fPhotonHist_Wavelength) {
        fPhotonHist_Wavelength->Write();
        G4cout << "Photon wavelength histogram written with " << fPhotonHist_Wavelength->GetEntries() << " entries" << G4endl;
        fPhotonHist_Wavelength = nullptr;
      }

      G4cout << "ROOT file closed with " << fTree->GetEntries() << " events" << G4endl;

      fTree = nullptr;  // Tree will be deleted by ROOT file
      fRootFile->Close();
      fRootFile.reset();
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

  // Clear all data
  ClearEventData();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::BeginEvent(G4int eventID, G4double primaryEnergy,
                             G4int genieEntryID,
                             G4int incomingNuPdg,
                             G4double incomingNuKE)
{
  fEventID = eventID;
  fPrimaryEnergy = primaryEnergy / MeV; // Store in MeV
  fGenieEntryID = genieEntryID;
  fIncomingNuPdg = incomingNuPdg;
  fIncomingNuKE = incomingNuKE;
  ClearEventData();
  // Reset event-wide photon counter and chunk state for this event.
  fEventPhotonCount = 0;
  fPhotonsInChunk = 0;
  fChunkStartID = 0;
  fEventIDChunk = eventID;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::FlushPhotonChunk()
{
  if (!fRawTree) return;
  const Long64_t n = static_cast<Long64_t>(fPhotonPosX.size());
  if (n == 0) return;

  // Stamp the chunk for the reader. ChunkStartID is the global photon
  // index at the start of this chunk; fEventPhotonCount has already
  // been incremented n times since the last flush, so the chunk covers
  // [fEventPhotonCount - n, fEventPhotonCount).
  fEventIDChunk = fEventID;
  fChunkStartID = fEventPhotonCount - n;

  // Cast streamed G4double vectors into float write buffers. Reusing
  // member buffers avoids per-chunk allocations.
  fChunk_PosX.assign(fPhotonPosX.begin(), fPhotonPosX.end());
  fChunk_PosY.assign(fPhotonPosY.begin(), fPhotonPosY.end());
  fChunk_PosZ.assign(fPhotonPosZ.begin(), fPhotonPosZ.end());
  fChunk_DirX.assign(fPhotonDirX.begin(), fPhotonDirX.end());
  fChunk_DirY.assign(fPhotonDirY.begin(), fPhotonDirY.end());
  fChunk_DirZ.assign(fPhotonDirZ.begin(), fPhotonDirZ.end());
  fChunk_Time.assign(fPhotonTime.begin(), fPhotonTime.end());
  fChunk_Wavelength.assign(fPhotonWavelength.begin(), fPhotonWavelength.end());
  fChunk_PolX.assign(fPhotonPolX.begin(), fPhotonPolX.end());
  fChunk_PolY.assign(fPhotonPolY.begin(), fPhotonPolY.end());
  fChunk_PolZ.assign(fPhotonPolZ.begin(), fPhotonPolZ.end());
  if (fStoreProcessName) {
    fChunk_Process = fPhotonProcess;  // copy strings
  }

  fRawTree->Fill();

  // Clear the streamed vectors (NOT shrink_to_fit — keep capacity to
  // avoid re-allocating on every chunk). Retained accumulators
  // (fPhotonTimeRetained, fPhotonImmediateParentTrackID) are NOT
  // touched here — they are needed at EndEvent for segment-index.
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
  fChunk_Process.clear();

  fPhotonsInChunk = 0;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::EndEvent()
{
  // Drain any photons accumulated since the last FlushPhotonChunk
  // (the partial last chunk for the event). This makes
  // OpticalPhotonsRaw self-contained for this event before we Fill the
  // metadata tree below.
  if (fStoreIndividualPhotons && !fPhotonPosX.empty()) {
    FlushPhotonChunk();
  }

  // Total photons across the event = global counter (NOT current
  // fPhotonPosX.size() — that's been cleared by chunk flushes when
  // streaming is on).
  fNOpticalPhotons = static_cast<G4int>(fEventPhotonCount);

  // Skip track segment processing when individual photon storage is disabled
  // (used for lookup table generation where only histograms are needed).
  if (!fStoreIndividualPhotons) {
    if (fTree) {
      fTree->Fill();
    }
    return;
  }

  // === Output segments for every G4 track ===
  // No "meaningful tracks" filter — emit one row per G4 step (or one
  // per merged sub-step group when fEmitRawSegments=false). LUCiD
  // derives the meaningful-track view via Segment_TrackID +
  // Segment_NCherenkov.
  //
  // Merging criteria (only used when fEmitRawSegments=false):
  //   - For tracks ≥ 10 MeV: minimum 10 mm length OR direction change > 2°
  //   - For tracks < 10 MeV (or e±): merge until energy loss ≥ 1 MeV
  const G4double minSegmentLength = 10.0;  // mm
  const G4double maxAngleForMerge = 2.0 * M_PI / 180.0;  // 2 degrees in radians
  const G4double lowEnergyThreshold = 10.0;  // MeV - tracks below this use edep-based merging
  const G4double minEdepForLowEnergy = 1.0;  // MeV - minimum edep before saving segment for low-E tracks

  G4int segmentOffset = 0;

  // Per-track lookup: unmerged sub-step index -> global merged segment index.
  // Built during the merge loop below, consumed afterwards to fill
  // fPhoton_SegmentIndex.
  std::map<G4int, std::vector<G4int>> trackUnmergedToMergedGlobal;

  // Iterate every track in fAllTrackSegments (std::map iteration is
  // track-id ascending, which is chronological).
  for (const auto& trackPair : fAllTrackSegments) {
    G4int trackID = trackPair.first;
    const TrackSegmentInfo& info = trackPair.second;

    bool isLowEnergy = (info.initialEnergy / MeV) < lowEnergyThreshold;
    // Electrons / positrons multiple-scatter on essentially every step,
    // so the geometric (angle / length) criterion fires constantly and
    // produces an absurd number of segments per EM track. Route any e±
    // through the edep-based merger regardless of initial energy.
    bool isElectron = (std::abs(info.pdgCode) == 11);
    bool useEdepMerging = isLowEnergy || isElectron;

    // Merge segments for this track
    std::vector<TrackSegment> mergedSegments;
    std::vector<G4int> unmergedToMergedLocal;
    unmergedToMergedLocal.reserve(info.segments.size());

    if (fEmitRawSegments) {
      // Raw mode: every G4 sub-step is its own segment. The Python-side
      // merger in LUCiD (lucid/sources/segment_grouping.py) reapplies the
      // logic below to produce group_id.
      mergedSegments = info.segments;
      for (size_t i = 0; i < info.segments.size(); ++i) {
        unmergedToMergedLocal.push_back(static_cast<G4int>(i));
      }
    } else if (!info.segments.empty()) {
      TrackSegment current = info.segments[0];
      G4int currentMergedLocal = 0;
      unmergedToMergedLocal.push_back(currentMergedLocal);

      for (size_t i = 1; i < info.segments.size(); i++) {
        const TrackSegment& next = info.segments[i];

        bool shouldSave = false;

        if (useEdepMerging) {
          // Low energy or e± track: merge until edep >= 1 MeV
          shouldSave = (current.edep >= minEdepForLowEnergy);
        } else {
          // Normal track: use length and angle criteria
          G4double dx = current.endX - current.startX;
          G4double dy = current.endY - current.startY;
          G4double dz = current.endZ - current.startZ;
          G4double currentLength = std::sqrt(dx*dx + dy*dy + dz*dz);

          // Calculate direction change
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
          ++currentMergedLocal;
        } else {
          // Merge: extend end position, accumulate edep, keep original start and direction.
          // betaStart from the first sub-step is preserved (current.betaStart unchanged);
          // nCherenkov accumulates across merged sub-steps.
          current.endX = next.endX;
          current.endY = next.endY;
          current.endZ = next.endZ;
          current.edep += next.edep;
          current.nCherenkov += next.nCherenkov;
        }
        unmergedToMergedLocal.push_back(currentMergedLocal);
      }
      // Don't forget the last segment
      mergedSegments.push_back(current);
    }

    std::vector<G4int>& globalMap = trackUnmergedToMergedGlobal[trackID];
    globalMap.reserve(unmergedToMergedLocal.size());
    for (G4int local : unmergedToMergedLocal) {
      globalMap.push_back(segmentOffset + local);
    }

    // Output merged segments for this track, with track id inlined.
    for (const TrackSegment& seg : mergedSegments) {
      fSegment_TrackID.push_back(info.trackID);
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
      fSegment_BetaStart.push_back(seg.betaStart);
      fSegment_NCherenkov.push_back(seg.nCherenkov);
    }

    segmentOffset += mergedSegments.size();
  }
  fNSegments = segmentOffset;

  // === Per-photon merged-segment index ===
  // For each photon, look up its immediate parent's segments by time and remap
  // through the (trackID, unmerged sub-step idx) -> global merged segment idx
  // table built during the merge loop. After dropping the meaningful-tracks
  // filter, every track has segments recorded, so the -1 sentinel never
  // fires (kept defensively for any edge case).
  //
  // Read photon counts/parents/times from the *retained* event-wide
  // accumulators. fPhotonPosX / fPhotonTime are the streamed vectors and
  // have already been flushed to OpticalPhotonsRaw and cleared by the
  // partial-chunk flush at the top of EndEvent().
  const size_t nPhotons = fPhotonImmediateParentTrackID.size();
  fPhoton_SegmentIndex.resize(nPhotons, -1);
  for (size_t p = 0; p < nPhotons; ++p) {
    G4int parentID = fPhotonImmediateParentTrackID[p];
    auto remapIt = trackUnmergedToMergedGlobal.find(parentID);
    if (remapIt == trackUnmergedToMergedGlobal.end()) continue;
    auto segsIt = fAllTrackSegments.find(parentID);
    if (segsIt == fAllTrackSegments.end()) continue;
    const auto& segs = segsIt->second.segments;
    if (segs.empty()) continue;

    // fPhotonTimeRetained[p] is in ns (set in AddOpticalPhoton via time/ns).
    // segs[i].time is also in ns (set in AddTrackSegment via time/ns).
    G4double pt = fPhotonTimeRetained[p];
    // Largest segment idx with seg.time <= pt — that is the emitting step.
    int lo = 0, hi = static_cast<int>(segs.size()) - 1, found = -1;
    while (lo <= hi) {
      int mid = (lo + hi) / 2;
      if (segs[mid].time <= pt) { found = mid; lo = mid + 1; }
      else { hi = mid - 1; }
    }
    if (found < 0) continue;
    const auto& globalMap = remapIt->second;
    if (found >= static_cast<int>(globalMap.size())) continue;
    fPhoton_SegmentIndex[p] = globalMap[found];
  }

  // === Track info — every registered Geant4 track ===
  // The Python categorizer needs the full ancestry chain (parent_id +
  // pdg) for every intermediate track in order to walk back to the
  // categorized ancestor. std::map iteration is track-id ascending,
  // which is chronological order. Optical photons were excluded at
  // RegisterTrack time.
  for (const auto& pair : fTrackRegistry) {
    const TrackInfo& info = pair.second;
    fTrackInfo_TrackID.push_back(info.trackID);
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
    fTrackInfo_CreatorProcess.push_back(std::string(info.creatorProcess));
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
                                  G4int immediateParentTrackID)
{
  // Always fill the 2D histogram for aggregated data
  if (fPhotonHist_AngleDistance) {
    // Calculate distance from origin
    G4double distance = std::sqrt(x*x + y*y + z*z) / mm;  // Convert to mm

    // Calculate opening angle with respect to muon direction (0,0,1)
    // Assume muon travels along +Z axis
    G4double muon_z = 1.0;  // Unit vector in Z direction
    G4double dot_product = dz * muon_z;
    G4double opening_angle = std::acos(std::max(-1.0, std::min(1.0, dot_product)));

    fPhotonHist_AngleDistance->Fill(opening_angle, distance);

    // Fill time vs distance histogram
    G4double time_ns = time / ns;
    fPhotonHist_TimeDistance->Fill(distance, time_ns);
  }

  // Fill wavelength histogram
  if (fPhotonHist_Wavelength) {
    G4double wavelength_nm = wavelength / nm;
    fPhotonHist_Wavelength->Fill(wavelength_nm);
  }

  // Conditionally store individual photon data
  if (fStoreIndividualPhotons) {
    // ---- Streamed: flushed by FlushPhotonChunk every fPhotonChunkSize ----
    fPhotonPosX.push_back(x / mm);   // Store in mm
    fPhotonPosY.push_back(y / mm);
    fPhotonPosZ.push_back(z / mm);
    fPhotonDirX.push_back(dx);
    fPhotonDirY.push_back(dy);
    fPhotonDirZ.push_back(dz);
    fPhotonTime.push_back(time / ns); // Store in ns
    fPhotonWavelength.push_back(wavelength / nm); // Store in nm
    fPhotonPolX.push_back(polX);
    fPhotonPolY.push_back(polY);
    fPhotonPolZ.push_back(polZ);
    if (fStoreProcessName) {
      fPhotonProcess.push_back(std::string(process));
    }

    ++fEventPhotonCount;

    // Retained-across-event arrays needed by the segment-index compute
    // at EndEvent.
    fPhotonImmediateParentTrackID.push_back(immediateParentTrackID);
    fPhotonTimeRetained.push_back(time / ns);

    // Auto-flush when the chunk is full (skipped when streaming is off
    // for debug/A-B comparison; in that mode the only flush is at
    // EndEvent so the chunk size grows to NPhotons).
    if (fStreamPhotonsChunked &&
        static_cast<Long64_t>(fPhotonPosX.size()) >= fPhotonChunkSize) {
      FlushPhotonChunk();
    }
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::AddEnergyDeposit(G4double x, G4double y, G4double z,
                                  G4double energy, G4double stepLength,
                                  const G4String& particleName)
{
  // Histogram-only. Skip photons (gamma and opticalphoton) - dE/dx is
  // not meaningful for them.
  if (!fdEdxHist_Distance) return;
  if (particleName == "gamma" || particleName == "opticalphoton") return;
  // Only fill if step length is positive to avoid division by zero.
  if (stepLength <= 0.0) return;

  G4double distance = std::sqrt(x*x + y*y + z*z) / mm;  // Convert to mm
  G4double stepLength_mm = stepLength / mm;
  G4double dEdx = (energy / keV) / stepLength_mm;

  // Fill histogram: X-axis is dE/dx, Y-axis is distance
  fdEdxHist_Distance->Fill(dEdx, distance);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DataManager::RegisterTrack(G4int trackID, const G4String& particleName, G4int parentID,
                               const G4ThreeVector& position, const G4ThreeVector& momentum,
                               G4double energy, G4double time, G4int pdgCode,
                               const G4String& creatorProcess)
{
  TrackInfo info;
  info.trackID = trackID;
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
  info.creatorProcess = creatorProcess;
  info.preMomentumDir = momentum.unit();  // Store initial momentum

  fTrackRegistry[trackID] = info;
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
                                  G4double edep, G4double time,
                                  G4double betaStart, G4int nCherenkov)
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
  seg.betaStart = betaStart;          // dimensionless (β = v/c)
  seg.nCherenkov = nCherenkov;        // count, no units

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
  fPhoton_SegmentIndex.clear();
  fPhotonImmediateParentTrackID.clear();
  fPhotonTimeRetained.clear();
  fEventPhotonCount = 0;
  fPhotonsInChunk = 0;
  fChunkStartID = 0;

  // Clear temporary track segment storage
  fAllTrackSegments.clear();

  // Clear segments output
  fNSegments = 0;
  fSegment_TrackID.clear();
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
  fSegment_BetaStart.clear();
  fSegment_NCherenkov.clear();

  // Clear track info arrays
  fTrackInfo_TrackID.clear();
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
  fTrackInfo_CreatorProcess.clear();

  // Clear track registry for new event
  ClearTrackRegistry();
}

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

  // Clean up ROOT objects - histograms are already handled by Finalize().
  fPhotonHist_AngleDistance = nullptr;
  fdEdxHist_Distance = nullptr;
  fPhotonHist_TimeDistance = nullptr;
  fPhotonHist_Wavelength = nullptr;
  fTree = nullptr;
  fRootFile.reset();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim
