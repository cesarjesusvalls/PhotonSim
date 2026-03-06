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
    
    void BeginEvent(G4int eventID, G4double primaryEnergy);
    void EndEvent();
    
    void AddOpticalPhoton(G4double x, G4double y, G4double z,
                         G4double dx, G4double dy, G4double dz,
                         G4double time, G4double wavelength,
                         G4double polX, G4double polY, G4double polZ,
                         const G4String& process,
                         const std::vector<G4int>& genealogy);

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
                        G4double edep, G4double time);
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
    bool GetStoreIndividualPhotons() const { return fStoreIndividualPhotons; }
    bool GetStoreIndividualEdeps() const { return fStoreIndividualEdeps; }
    
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
    
    // Event-level data
    G4int fEventID = 0;
    G4double fPrimaryEnergy = 0.0;
    G4int fNOpticalPhotons = 0;
    G4int fNEnergyDeposits = 0;
    
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
    
    // 2D ROOT histograms for aggregated data (500x500 bins)
    TH2D* fPhotonHist_AngleDistance = nullptr;  // Opening angle vs distance
    TH2D* fdEdxHist_Distance = nullptr;         // dE/dx vs distance
    TH2D* fPhotonHist_TimeDistance = nullptr;   // Photon time vs distance

    // 1D ROOT histogram for wavelength distribution
    TH1D* fPhotonHist_Wavelength = nullptr;     // Photon wavelength distribution
    
    // Output filename
    G4String fOutputFilename = "optical_photons.root";
    
    void ClearEventData();
};

}  // namespace PhotonSim

#endif