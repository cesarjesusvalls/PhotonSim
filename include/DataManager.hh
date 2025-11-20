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
  kGammaShower = 3
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
                         const G4String& process,
                         const std::vector<G4int>& genealogy);

    void AddEnergyDeposit(G4double x, G4double y, G4double z,
                         G4double energy, G4double time,
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

    // Get next SubID for a category
    G4int GetNextPrimaryID() { return fNPrimaries++; }
    G4int GetNextDecayElectronID() { return fNDecayElectrons++; }
    G4int GetNextSecondaryPionID() { return fNSecondaryPions++; }
    G4int GetNextGammaShowerID() { return fNGammaShowers++; }
    
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
    std::vector<std::string> fPhotonProcess;

    // Label system: unique genealogies and their photons
    G4int fNLabels = 0;
    std::vector<G4int> fLabel_GenealogySize;
    std::vector<G4int> fLabel_GenealogyData;
    std::vector<G4int> fLabel_PhotonIDsSize;
    std::vector<G4int> fLabel_PhotonIDsData;

    // Internal map for building labels during event
    std::map<std::vector<G4int>, std::vector<G4int>> fGenealogyToPhotonIDs;
    
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
    G4int fNGammaShowers = 0;

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
    TH2D* fEdepHist_DistanceEnergy = nullptr;   // Distance vs energy deposit
    TH2D* fPhotonHist_TimeDistance = nullptr;   // Photon time vs distance

    // 1D ROOT histogram for wavelength distribution
    TH1D* fPhotonHist_Wavelength = nullptr;     // Photon wavelength distribution
    
    // Output filename
    G4String fOutputFilename = "optical_photons.root";
    
    void ClearEventData();
};

}  // namespace PhotonSim

#endif