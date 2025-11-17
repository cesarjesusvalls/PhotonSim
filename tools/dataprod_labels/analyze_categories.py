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
    """Analyze PhotonSim category classification output"""

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

        # Count categories
        cat_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for i in range(tree.NOpticalPhotons):
            cat = tree.PhotonCategory[i]
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            total_by_category[cat] += 1

        total_photons += tree.NOpticalPhotons

        print(f"Event {evt}:")
        print(f"  Primary Energy: {tree.PrimaryEnergy} MeV")
        print(f"  Total photons: {tree.NOpticalPhotons}")

        # Photon breakdown by category
        print(f"  Photon breakdown:")
        for cat in sorted(cat_counts.keys()):
            if cat_counts[cat] > 0:
                pct = 100.0 * cat_counts[cat] / tree.NOpticalPhotons
                print(f"    {category_names[cat]}: {cat_counts[cat]:6d} ({pct:5.1f}%)")

        # Track information
        print(f"  Categorized tracks: {len(tree.TrackInfo_TrackID)}")

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

        # Collect and print all unique genealogies for this event
        if tree.NOpticalPhotons > 0:
            # Dictionary to track: genealogy_tuple -> (category, subID, count)
            genealogy_info = {}
            data_idx = 0

            for i in range(len(tree.PhotonGenealogySize)):
                size = tree.PhotonGenealogySize[i]
                gen = tuple([tree.PhotonGenealogyData[data_idx + j] for j in range(size)])
                cat = tree.PhotonCategory[i]
                subid = tree.PhotonSubCategoryID[i]

                # Track unique genealogies with their info
                if gen not in genealogy_info:
                    genealogy_info[gen] = {'category': cat, 'subID': subid, 'count': 0}
                genealogy_info[gen]['count'] += 1

                data_idx += size

            # Print all unique genealogies
            print(f"  Unique genealogies in this event: {len(genealogy_info)}")
            for gen, info in sorted(genealogy_info.items(), key=lambda x: x[1]['count'], reverse=True):
                gen_list = list(gen)
                print(f"    Genealogy {gen_list}: Category={category_names.get(info['category'], info['category'])}, "
                      f"SubID={info['subID']}, Photons={info['count']}")

                # Print track info for each track in this genealogy
                for track_id in gen_list:
                    if track_id in track_info_map:
                        t = track_info_map[track_id]
                        pdg_name = get_pdg_name(t.get('pdg', 0))
                        print(f"      -> Track {track_id}: PDG={t.get('pdg', 'N/A')} ({pdg_name}), "
                              f"Category={category_names.get(t['category'], t['category'])}, "
                              f"SubID={t['subID']}, E={t['energy']:.3f} MeV, Parent={t['parent']}")
                    else:
                        print(f"      -> Track {track_id}: [No track info available]")

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

    # Check genealogy data integrity
    print(f"\nData integrity check:")
    tree.GetEntry(0)
    total_gen_size = sum([tree.PhotonGenealogySize[i]
                          for i in range(len(tree.PhotonGenealogySize))])
    genealogy_ok = (total_gen_size == len(tree.PhotonGenealogyData))
    print(f"  Genealogy structure: {'OK' if genealogy_ok else 'ERROR'}")
    print(f"  Expected genealogy entries: {total_gen_size}")
    print(f"  Actual genealogy entries: {len(tree.PhotonGenealogyData)}")

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
