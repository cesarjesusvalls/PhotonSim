import ROOT
import numpy as np

def get_pdg_name(pdg_code):
    """Convert PDG code to particle name"""
    pdg_names = {
        11: "e-",
        -11: "e+",
        13: "mu-",
        -13: "mu+",
        22: "gamma",
        111: "pi0",
        211: "pi+",
        -211: "pi-",
        321: "K+",
        -321: "K-",
        2212: "proton",
        -2212: "antiproton",
        2112: "neutron",
        -2112: "antineutron",
        0: "geantino",
    }
    return pdg_names.get(pdg_code, f"PDG_{pdg_code}")

def analyze_root_file(filename):
    """Analyze PhotonSim label-centric classification output"""

    f = ROOT.TFile(filename, "READ")
    tree = f.Get("OpticalPhotons")

    category_names = {
        -1: "Uncategorized",
        0: "Primary",
        1: "DecayElectron",
        2: "SecondaryPion",
        3: "GammaShower"
    }

    print(f"{'='*60}")
    print(f"Analysis of: {filename}")
    print(f"{'='*60}\n")
    print(f"Total events: {tree.GetEntries()}\n")

    # Summary statistics
    total_photons = 0
    total_by_category = {0: 0, 1: 0, 2: 0, 3: 0}

    for evt in range(tree.GetEntries()):
        tree.GetEntry(evt)

        print(f"Event {evt}:")
        print(f"  Primary Energy: {tree.PrimaryEnergy} MeV")
        print(f"  Total photons: {tree.NOpticalPhotons}")
        total_photons += tree.NOpticalPhotons

        # Build track ID to track info mapping for easy lookup
        track_info_map = {}
        for i in range(len(tree.TrackInfo_TrackID)):
            track_id = tree.TrackInfo_TrackID[i]
            track_info_map[track_id] = {
                'trackID': track_id,
                'category': tree.TrackInfo_Category[i],
                'subID': tree.TrackInfo_SubID[i],
                'energy': tree.TrackInfo_Energy[i],
                'parent': tree.TrackInfo_ParentTrackID[i],
                'pos': (tree.TrackInfo_PosX[i], tree.TrackInfo_PosY[i], tree.TrackInfo_PosZ[i]),
                'dir': (tree.TrackInfo_DirX[i], tree.TrackInfo_DirY[i], tree.TrackInfo_DirZ[i]),
                'time': tree.TrackInfo_Time[i],
                'pdg': tree.TrackInfo_PDG[i]
            }

        # Track information
        print(f"  Categorized tracks (with parents): {len(tree.TrackInfo_TrackID)}")

        # Group tracks by category
        track_by_cat = {}
        for i in range(len(tree.TrackInfo_TrackID)):
            cat = tree.TrackInfo_Category[i]
            if cat not in track_by_cat:
                track_by_cat[cat] = []

            track_info = {
                'trackID': tree.TrackInfo_TrackID[i],
                'subID': tree.TrackInfo_SubID[i],
                'energy': tree.TrackInfo_Energy[i],
                'parent': tree.TrackInfo_ParentTrackID[i],
                'pos': (tree.TrackInfo_PosX[i], tree.TrackInfo_PosY[i], tree.TrackInfo_PosZ[i]),
                'dir': (tree.TrackInfo_DirX[i], tree.TrackInfo_DirY[i], tree.TrackInfo_DirZ[i]),
                'time': tree.TrackInfo_Time[i],
                'pdg': tree.TrackInfo_PDG[i]
            }
            track_by_cat[cat].append(track_info)

        # Print track details
        for cat in sorted(track_by_cat.keys()):
            tracks = track_by_cat[cat]
            print(f"    {category_names[cat]} ({len(tracks)} tracks):")
            for t in tracks:
                pdg_name = get_pdg_name(t.get('pdg', 0))
                print(f"      Track {t['trackID']}: SubID={t['subID']}, PDG={t.get('pdg', 'N/A')} ({pdg_name})")
                print(f"        Energy={t['energy']:.3f} MeV, Time={t['time']:.3f} ns, Parent={t['parent']}")
                print(f"        Pos=({t['pos'][0]:.2f}, {t['pos'][1]:.2f}, {t['pos'][2]:.2f}) mm")
                print(f"        Dir=({t['dir'][0]:.4f}, {t['dir'][1]:.4f}, {t['dir'][2]:.4f})")

        # Parse label-centric structure
        print(f"  Number of labels: {tree.NLabels}")

        # Unflatten genealogy and photon ID data
        gen_idx = 0
        photon_idx = 0

        cat_counts = {0: 0, 1: 0, 2: 0, 3: 0}

        for label_i in range(tree.NLabels):
            # Extract genealogy for this label
            gen_size = tree.Label_GenealogySize[label_i]
            genealogy = []
            for j in range(gen_size):
                genealogy.append(tree.Label_GenealogyData[gen_idx + j])
            gen_idx += gen_size

            # Extract photon IDs for this label
            photon_ids_size = tree.Label_PhotonIDsSize[label_i]
            photon_ids = []
            for j in range(photon_ids_size):
                photon_ids.append(tree.Label_PhotonIDsData[photon_idx + j])
            photon_idx += photon_ids_size

            # Derive category and subID from last track in genealogy
            if len(genealogy) > 0:
                last_track_id = genealogy[-1]
                if last_track_id in track_info_map:
                    category = track_info_map[last_track_id]['category']
                    subID = track_info_map[last_track_id]['subID']
                else:
                    category = -1
                    subID = -1
            else:
                category = -1
                subID = -1

            # Count photons by category
            if category in cat_counts:
                cat_counts[category] += len(photon_ids)

            # Print label information
            print(f"    Label {label_i}: Category={category_names.get(category, category)}, SubID={subID}")
            print(f"      Genealogy: {genealogy}")
            print(f"      Number of photons: {len(photon_ids)}")

            # Print track info for each track in genealogy
            for track_id in genealogy:
                if track_id in track_info_map:
                    t = track_info_map[track_id]
                    pdg_name = get_pdg_name(t.get('pdg', 0))
                    print(f"        -> Track {track_id}: PDG={t.get('pdg', 'N/A')} ({pdg_name}), "
                          f"Category={category_names.get(t['category'], t['category'])}, "
                          f"SubID={t['subID']}, E={t['energy']:.3f} MeV, Parent={t['parent']}")
                else:
                    print(f"        -> Track {track_id}: [No track info available]")

        # Photon breakdown by category (derived from labels)
        print(f"  Photon breakdown by category:")
        for cat in sorted(cat_counts.keys()):
            if cat_counts[cat] > 0:
                pct = 100.0 * cat_counts[cat] / tree.NOpticalPhotons if tree.NOpticalPhotons > 0 else 0
                print(f"    {category_names[cat]}: {cat_counts[cat]:6d} ({pct:5.1f}%)")
                total_by_category[cat] += cat_counts[cat]

        print()

    # Overall summary
    print(f"{'='*60}")
    print(f"Overall Summary:")
    print(f"{'='*60}")
    print(f"Total photons across all events: {total_photons}")
    print(f"\nPhoton distribution by category:")
    for cat in sorted(total_by_category.keys()):
        count = total_by_category[cat]
        if count > 0:
            pct = 100.0 * count / total_photons if total_photons > 0 else 0
            print(f"  {category_names[cat]:20s}: {count:8d} ({pct:5.1f}%)")

    # Data integrity check
    print(f"\nData integrity check:")
    tree.GetEntry(0)
    total_gen_size = sum([tree.Label_GenealogySize[i]
                          for i in range(len(tree.Label_GenealogySize))])
    genealogy_ok = (total_gen_size == len(tree.Label_GenealogyData))
    print(f"  Genealogy structure: {'OK' if genealogy_ok else 'ERROR'}")
    print(f"  Expected genealogy entries: {total_gen_size}")
    print(f"  Actual genealogy entries: {len(tree.Label_GenealogyData)}")

    total_photon_ids_size = sum([tree.Label_PhotonIDsSize[i]
                                 for i in range(len(tree.Label_PhotonIDsSize))])
    photon_ids_ok = (total_photon_ids_size == tree.NOpticalPhotons)
    print(f"  Photon IDs structure: {'OK' if photon_ids_ok else 'ERROR'}")
    print(f"  Sum of label photon counts: {total_photon_ids_size}")
    print(f"  Total optical photons: {tree.NOpticalPhotons}")

    f.Close()
    print()


if __name__ == "__main__":
    import sys

    # Analyze files
    files = ["test_pions.root", "test_categories.root"]

    # Allow command line arguments
    if len(sys.argv) > 1:
        files = sys.argv[1:]

    for filename in files:
        try:
            analyze_root_file(filename)
        except Exception as e:
            print(f"Error analyzing {filename}: {e}\n")
            import traceback
            traceback.print_exc()
