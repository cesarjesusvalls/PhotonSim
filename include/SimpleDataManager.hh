//
/// \file PhotonSim/include/SimpleDataManager.hh
/// \brief Simple data manager without ROOT dependencies

#ifndef SimpleDataManager_h
#define SimpleDataManager_h 1

#include "G4String.hh"
#include "G4Types.hh"
#include <fstream>
#include <vector>

namespace PhotonSim
{

/// Simple data manager that outputs to CSV files instead of ROOT

class SimpleDataManager
{
  public:
    static SimpleDataManager* GetInstance();
    
    void Initialize(const G4String& filename);
    void Finalize();
    
    void BeginEvent(G4int eventID, G4double primaryEnergy);
    void EndEvent();
    
    void AddOpticalPhoton(G4double x, G4double y, G4double z,
                         G4double dx, G4double dy, G4double dz,
                         G4double time, const G4String& process);
    
  private:
    SimpleDataManager() = default;
    ~SimpleDataManager() = default;
    
    static SimpleDataManager* fInstance;
    
    std::ofstream fOutputFile;
    std::ofstream fSummaryFile;
    
    // Current event data
    G4int fCurrentEventID = 0;
    G4double fCurrentPrimaryEnergy = 0.0;
    G4int fPhotonCount = 0;
    
    bool fInitialized = false;
};

}  // namespace PhotonSim

#endif