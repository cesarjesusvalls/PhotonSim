#ifndef PhotonSimRooTrackerReader_h
#define PhotonSimRooTrackerReader_h 1

#include "globals.hh"
#include "Rtypes.h"  // Long64_t, Int_t, Double_t

#include <vector>
#include <string>

class TFile;
class TTree;

namespace PhotonSim
{

/// One final-state particle extracted from a GENIE rooTracker entry.
/// Momenta are stored in MeV (GENIE's GeV converted once at read time).
struct GenieParticle {
  G4int pdg;
  G4double px;
  G4double py;
  G4double pz;
  G4double E;
};

/// Reads a GENIE gRooTracker TTree (as produced by `gntpc -f rootracker`)
/// one event at a time, exposing the final-state particles (StdHepStatus == 1)
/// for injection as Geant4 primaries. The incoming neutrino 4-momentum is
/// surfaced separately so downstream bookkeeping can log true primary
/// energy.
class RooTrackerReader
{
  public:
    RooTrackerReader();
    ~RooTrackerReader();

    /// Open the rootracker file. Returns false if the TFile/TTree cannot be
    /// loaded.
    G4bool Open(const std::string& path);
    G4bool IsOpen() const { return fTree != nullptr; }
    const std::string& GetPath() const { return fPath; }

    Long64_t GetNumEvents() const;

    /// Load the entry at index `i`. Populates the particle list and the
    /// incoming-neutrino cache. Returns false if i is out of range or the
    /// entry fails to read.
    G4bool LoadEvent(Long64_t i);

    const std::vector<GenieParticle>& FinalStateParticles() const { return fFinalState; }

    /// Incoming neutrino kinetic energy in MeV (or 0 if no status-0 lepton
    /// was found in the last loaded entry).
    G4double IncomingNeutrinoKE_MeV() const { return fNuKE_MeV; }
    G4int IncomingNeutrinoPdg() const { return fNuPdg; }

  private:
    std::string fPath;
    TFile* fFile = nullptr;
    TTree* fTree = nullptr;

    static constexpr int kMaxParticles = 4096;

    Int_t   fStdHepN = 0;
    Int_t   fStdHepPdg[kMaxParticles] = {};
    Int_t   fStdHepStatus[kMaxParticles] = {};
    Double_t fStdHepP4[kMaxParticles][4] = {};

    std::vector<GenieParticle> fFinalState;
    G4double fNuKE_MeV = 0.0;
    G4int fNuPdg = 0;
};

}  // namespace PhotonSim

#endif
