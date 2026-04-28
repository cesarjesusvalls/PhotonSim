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

#ifndef PhotonSimDataManager_h
#define PhotonSimDataManager_h 1

#include "G4String.hh"
#include "G4Types.hh"
#include "G4ThreeVector.hh"
#include "Rtypes.h"   // Long64_t
#include <vector>
#include <memory>
#include <string>
#include <map>

class TFile;
class TTree;
class TH2D;
class TH1D;

namespace PhotonSim
{

/// Category enumeration for photon classification
enum PhotonCategory {
  kPrimary = 0,
  kDecayElectron = 1,
  kSecondaryPion = 2,
  kGamma = 3
};

/// Structure to hold track information for categorized particles
struct TrackInfo {
  G4int trackID;
  G4int category;
  G4int subID;
  G4double posX, posY, posZ;
  G4double dirX, dirY, dirZ;
  G4double energy;
  G4double time;
  G4int parentTrackID;
  G4String particleName;
  G4int pdgCode;

  // Synchronized triplet for pion deflection detection
  G4ThreeVector preMomentumDir;     // Momentum direction at previous step
  G4ThreeVector preMomentumPos;     // Position where preMomentumDir was recorded
  G4double preMomentumTime = 0.0;   // Time when preMomentumDir was recorded

  // For photon relabeling in deflection handling
  G4bool needsPhotonRelabeling = false;
  G4int originalParentID = -1;
  G4double relabelingTime = 0.0;
};

/// Structure to hold a single track segment (one G4 step)
struct TrackSegment {
  G4double startX, startY, startZ;  // Pre-step position
  G4double endX, endY, endZ;        // Post-step position
  G4double dirX, dirY, dirZ;        // Direction at pre-step
  G4double edep;                    // Energy deposited in this step
  G4double time;                    // Time at pre-step
  G4double betaStart;               // β = v/c at pre-step (for Cherenkov physics)
  G4int    nCherenkov;              // Cherenkov photons emitted in this step
};

/// Structure to hold all segment info for a track during event processing
struct TrackSegmentInfo {
  G4int trackID;
  G4int parentID;
  G4int pdgCode;
  G4double initialEnergy;           // Kinetic energy at creation
  G4String particleName;
  G4int cherenkovCount = 0;         // Number of Cherenkov photons produced
  std::vector<TrackSegment> segments;
};

/// Singleton class to manage ROOT data output for optical photons

class DataManager
{
  public:
    static DataManager* GetInstance();
    static void DeleteInstance();
    
    void Initialize(const G4String& filename = "");
    void Finalize();
    
    // Reset method for proper cleanup
    void Reset();
    
    void BeginEvent(G4int eventID, G4double primaryEnergy,
                    G4int genieEntryID = -1,
                    G4int incomingNuPdg = 0,
                    G4double incomingNuKE = 0.0);
    void EndEvent();
    
    void AddOpticalPhoton(G4double x, G4double y, G4double z,
                         G4double dx, G4double dy, G4double dz,
                         G4double time, G4double wavelength,
                         G4double polX, G4double polY, G4double polZ,
                         const G4String& process,
                         const std::vector<G4int>& genealogy,
                         G4int immediateParentTrackID = 0);

    void AddEnergyDeposit(G4double x, G4double y, G4double z,
                         G4double energy, G4double stepLength,
                         G4double time,
                         const G4String& particleName,
                         G4int trackID = -1,
                         G4int parentID = -1);

    // Enhanced track registry for category-based system
    void RegisterTrack(G4int trackID, const G4String& particleName, G4int parentID,
                      const G4ThreeVector& position, const G4ThreeVector& momentum,
                      G4double energy, G4double time, G4int pdgCode);
    void UpdateTrackCategory(G4int trackID, G4int category, G4int subID, G4int categoryParentTrackID);
    void UpdatePionMomentum(G4int trackID, const G4ThreeVector& momentumDir,
                           const G4ThreeVector& position, G4double time);
    TrackInfo* GetTrackInfo(G4int trackID);
    std::vector<G4int> BuildGenealogy(G4int trackID);
    void ClearTrackRegistry();

    // Photon relabeling for deflection handling
    void RelabelPhotonsForDeflection(G4int newTrackID, G4int oldTrackID, G4double deflectionTime);

    // Track segment system for meaningful tracks
    void AddTrackSegment(G4int trackID, G4int parentID, G4int pdgCode,
                        const G4String& particleName, G4double initialEnergy,
                        G4double startX, G4double startY, G4double startZ,
                        G4double endX, G4double endY, G4double endZ,
                        G4double dirX, G4double dirY, G4double dirZ,
                        G4double edep, G4double time,
                        G4double betaStart, G4int nCherenkov);
    void IncrementCherenkovCount(G4int trackID);
    std::vector<G4int> BuildExtendedGenealogy(G4int trackID);

    // Get next SubID for a category
    G4int GetNextPrimaryID() { return fNPrimaries++; }
    G4int GetNextDecayElectronID() { return fNDecayElectrons++; }
    G4int GetNextSecondaryPionID() { return fNSecondaryPions++; }
    G4int GetNextGammaID() { return fNGammas++; }
    
    // Control methods for individual data storage
    void SetStoreIndividualPhotons(bool store) { fStoreIndividualPhotons = store; }
    void SetStoreIndividualEdeps(bool store) { fStoreIndividualEdeps = store; }
    void SetStoreSegmentIndex(bool store) { fStoreSegmentIndex = store; }
    void SetStoreProcessName(bool store) { fStoreProcessName = store; }
    void SetStreamPhotonsChunked(bool stream) { fStreamPhotonsChunked = stream; }
    void SetEmitRawSegments(bool emit) { fEmitRawSegments = emit; }
    bool GetStoreIndividualPhotons() const { return fStoreIndividualPhotons; }
    bool GetStoreIndividualEdeps() const { return fStoreIndividualEdeps; }
    bool GetStoreSegmentIndex() const { return fStoreSegmentIndex; }
    bool GetStoreProcessName() const { return fStoreProcessName; }
    bool GetStreamPhotonsChunked() const { return fStreamPhotonsChunked; }
    bool GetEmitRawSegments() const { return fEmitRawSegments; }
    
    // Output filename control
    void SetOutputFilename(const G4String& filename) { fOutputFilename = filename; }
    G4String GetOutputFilename() const { return fOutputFilename; }

    // Debug output
    void PrintPionSummary(G4int eventID);

  private:
    DataManager() = default;
    ~DataManager();
    
    // Delete copy constructor and assignment operator
    DataManager(const DataManager&) = delete;
    DataManager& operator=(const DataManager&) = delete;
    
    static DataManager* fInstance;

    std::unique_ptr<TFile> fRootFile;
    TTree* fTree = nullptr;

    // Per-event metadata tree's sister tree: holds chunked per-photon
    // measurements. One entry = one chunk of up to fPhotonChunkSize photons.
    // EventID + ChunkStartID stamp each chunk so readers can locate the
    // photons that belong to a given event/global-id range.
    TTree* fRawTree = nullptr;
    G4int   fEventIDChunk  = -1;
    Long64_t fChunkStartID = 0;       // global photon ID at start of current chunk
    Long64_t fPhotonsInChunk = 0;     // grows as photons are appended; flushed at K
    Long64_t fEventPhotonCount = 0;   // total photons emitted in the current event,
                                      // used to derive the per-chunk start id.

    // Float-cast write buffers used inside FlushPhotonChunk(). Declared here
    // to avoid reallocating per chunk.
    std::vector<float> fChunk_PosX, fChunk_PosY, fChunk_PosZ;
    std::vector<float> fChunk_DirX, fChunk_DirY, fChunk_DirZ;
    std::vector<float> fChunk_Time, fChunk_Wavelength;
    std::vector<float> fChunk_PolX, fChunk_PolY, fChunk_PolZ;
    std::vector<std::string> fChunk_Process;
    
    // Event-level data
    G4int fEventID = 0;
    G4double fPrimaryEnergy = 0.0;
    G4int fNOpticalPhotons = 0;
    G4int fNEnergyDeposits = 0;

    // GENIE provenance (set per event by BeginEvent; -1 / 0 / NaN when the
    // event was fired from the particle gun). These are written as ROOT
    // branches so LUCiD's v5 labl can populate per_interaction/neutrino_*
    // fields without re-reading the rootracker.
    G4int    fGenieEntryID  = -1;
    G4int    fIncomingNuPdg = 0;
    G4double fIncomingNuKE  = 0.0;
    
    // Optical photon data (vectors for multiple photons per event)
    std::vector<G4double> fPhotonPosX;
    std::vector<G4double> fPhotonPosY;
    std::vector<G4double> fPhotonPosZ;
    std::vector<G4double> fPhotonDirX;
    std::vector<G4double> fPhotonDirY;
    std::vector<G4double> fPhotonDirZ;
    std::vector<G4double> fPhotonTime;
    std::vector<G4double> fPhotonWavelength;
    std::vector<G4double> fPhotonPolX;
    std::vector<G4double> fPhotonPolY;
    std::vector<G4double> fPhotonPolZ;
    std::vector<std::string> fPhotonProcess;

    // Per-photon link to the merged segment that emitted it. Filled at EndEvent
    // by walking each photon's immediate-parent track segments by time and
    // remapping unmerged sub-step -> merged segment index. -1 sentinel when the
    // parent track has no output segments (non-meaningful track or unknown).
    // Only written to ROOT when fStoreSegmentIndex is true.
    std::vector<G4int> fPhoton_SegmentIndex;

    // Transient: immediate Geant4 parent track ID per photon, captured at
    // creation. Used only inside EndEvent to look up the emitting segment;
    // not written to ROOT.
    std::vector<G4int> fPhotonImmediateParentTrackID;

    // Transient retained-across-event copy of photon emission times. The
    // streamed `fPhotonTime` vector gets flushed every fPhotonChunkSize
    // photons (so peak memory stays bounded), but the segment-index
    // compute at EndEvent needs every photon's time. We retain a parallel
    // copy here only when fStoreSegmentIndex is true. Not written to ROOT.
    std::vector<G4double> fPhotonTimeRetained;

    // Particle system: unique genealogies and their photons
    G4int fNParticles = 0;
    std::vector<G4int> fParticle_GenealogySize;
    std::vector<G4int> fParticle_GenealogyData;
    std::vector<G4int> fParticle_PhotonIDsSize;
    std::vector<G4int> fParticle_PhotonIDsData;

    // Internal map for building particles during event
    std::map<std::vector<G4int>, std::vector<G4int>> fGenealogyToPhotonIDs;

    // Extended genealogy per particle (all meaningful track IDs in ancestry)
    std::vector<G4int> fParticle_ExtGenealogySize;
    std::vector<G4int> fParticle_ExtGenealogyData;

    // Temporary storage for track segments during event (all tracks)
    std::map<G4int, TrackSegmentInfo> fAllTrackSegments;

    // Output: Meaningful tracks table (tracks contributing to Cherenkov emission)
    G4int fNMeaningfulTracks = 0;
    std::vector<G4int> fMTrack_TrackID;
    std::vector<G4int> fMTrack_ParentID;
    std::vector<G4int> fMTrack_PDG;
    std::vector<G4double> fMTrack_InitialEnergy;
    std::vector<std::string> fMTrack_ParticleName;
    std::vector<G4int> fMTrack_NCherenkov;       // Number of Cherenkov photons produced
    std::vector<G4int> fMTrack_SegmentOffset;    // Offset into segment arrays
    std::vector<G4int> fMTrack_NSegments;        // Number of segments for this track

    // Output: Segments table (all steps for meaningful tracks)
    G4int fNSegments = 0;
    std::vector<G4double> fSegment_StartX;
    std::vector<G4double> fSegment_StartY;
    std::vector<G4double> fSegment_StartZ;
    std::vector<G4double> fSegment_EndX;
    std::vector<G4double> fSegment_EndY;
    std::vector<G4double> fSegment_EndZ;
    std::vector<G4double> fSegment_DirX;
    std::vector<G4double> fSegment_DirY;
    std::vector<G4double> fSegment_DirZ;
    std::vector<G4double> fSegment_Edep;
    std::vector<G4double> fSegment_Time;
    std::vector<G4double> fSegment_BetaStart;    // β = v/c at segment start (after merging, taken from first sub-step)
    std::vector<G4int>    fSegment_NCherenkov;   // Cherenkov photons emitted in segment (sum across merged sub-steps)
    
    // Energy deposit data (vectors for multiple deposits per event)
    std::vector<G4double> fEdepPosX;
    std::vector<G4double> fEdepPosY;
    std::vector<G4double> fEdepPosZ;
    std::vector<G4double> fEdepEnergy;
    std::vector<G4double> fEdepTime;
    std::vector<std::string> fEdepParticle;
    std::vector<G4int> fEdepTrackID;
    std::vector<G4int> fEdepParentID;
    
    bool fFinalized = false;  // Flag to prevent double finalization

    // Enhanced track registry: map track IDs to full TrackInfo
    std::map<G4int, TrackInfo> fTrackRegistry;

    // Category counters for current event
    G4int fNPrimaries = 0;
    G4int fNDecayElectrons = 0;
    G4int fNSecondaryPions = 0;
    G4int fNGammas = 0;

    // Event-level track information (parallel arrays for categorized tracks)
    std::vector<G4int> fTrackInfo_TrackID;
    std::vector<G4int> fTrackInfo_Category;
    std::vector<G4int> fTrackInfo_SubID;
    std::vector<G4double> fTrackInfo_PosX;
    std::vector<G4double> fTrackInfo_PosY;
    std::vector<G4double> fTrackInfo_PosZ;
    std::vector<G4double> fTrackInfo_DirX;
    std::vector<G4double> fTrackInfo_DirY;
    std::vector<G4double> fTrackInfo_DirZ;
    std::vector<G4double> fTrackInfo_Energy;
    std::vector<G4double> fTrackInfo_Time;
    std::vector<G4int> fTrackInfo_ParentTrackID;
    std::vector<G4int> fTrackInfo_PDG;

    // Control flags for individual data storage
    bool fStoreIndividualPhotons = true;
    bool fStoreIndividualEdeps = true;
    // When true, fill and write Photon_SegmentIndex (one int32 per photon
    // pointing into Segment_*). Default off — opt-in for downstream
    // segment <-> sensor correspondence consumers.
    bool fStoreSegmentIndex = false;
    // When true, write PhotonProcess (Geant4 emission process name). Default
    // off — every photon is "Cerenkov" in the Cherenkov-only detector, so
    // storing it is dead weight unless scintillation/WLS materials are added.
    bool fStoreProcessName = false;
    // When true (default), flush photon chunks to OpticalPhotonsRaw every
    // fPhotonChunkSize photons during the event so peak vector RAM stays
    // bounded. When false, the only flush happens at EndEvent (chunk size
    // becomes effectively unbounded). Debug knob — same on-disk schema
    // either way.
    bool fStreamPhotonsChunked = true;
    // When true, skip the segment merger in EndEvent and emit one
    // Segment_* row per raw G4 step. Downstream (LUCiD) reapplies the
    // merger in Python and writes group_id alongside; the merger
    // becomes a Python-side label instead of a C++-side destruction.
    // Default true on this branch; existing C++ merger is kept compilable
    // for byte-identity verification and will be removed in a follow-up.
    bool fEmitRawSegments = true;
    // Chunk size for OpticalPhotonsRaw entries. 100,000 photons ≈ 4 MB of
    // active streamed-vector memory.
    static constexpr Long64_t fPhotonChunkSize = 100000;
    
    // 2D ROOT histograms for aggregated data (500x500 bins)
    TH2D* fPhotonHist_AngleDistance = nullptr;  // Opening angle vs distance
    TH2D* fdEdxHist_Distance = nullptr;         // dE/dx vs distance
    TH2D* fPhotonHist_TimeDistance = nullptr;   // Photon time vs distance

    // 1D ROOT histogram for wavelength distribution
    TH1D* fPhotonHist_Wavelength = nullptr;     // Photon wavelength distribution
    
    // Output filename
    G4String fOutputFilename = "optical_photons.root";
    
    void ClearEventData();

    // Flush the currently-buffered photons in the streamed `fPhoton*`
    // vectors out to OpticalPhotonsRaw as a single TTree entry, then
    // clear those vectors to bound peak memory. Called every
    // fPhotonChunkSize photons by AddOpticalPhoton (when streaming is
    // on), and once at EndEvent to drain the partial last chunk. Does
    // NOT touch fPhotonTime / fPhotonImmediateParentTrackID — those
    // are the retained accumulators used by the segment-index compute
    // at EndEvent.
    void FlushPhotonChunk();
};

}  // namespace PhotonSim

#endif