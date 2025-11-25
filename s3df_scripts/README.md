# S3DF Scripts for PhotonSim

Scripts for building, running, and managing PhotonSim jobs on the S3DF cluster at SLAC.

## Quick Start

```bash
# 1. Configure your paths
cp user_paths.sh.template user_paths.sh
vim user_paths.sh  # Edit with your paths

# 2. Build PhotonSim
./utils/build_photonsim.sh

# 3. Test with one job (doesn't submit)
./jobs/generate_jobs.sh -c ../macros/data_production_config/dataprod_single_neg_mu.json -t

# 4. Generate and submit all jobs
./jobs/generate_jobs.sh -c ../macros/data_production_config/dataprod_single_neg_mu.json -s

# 5. Monitor your jobs
./jobs/monitor_jobs.sh -w
```

## Directory Structure

```
s3df_scripts/
├── user_paths.sh.template     # Configuration template (copy to user_paths.sh)
├── utils/                     # Build and environment utilities
│   ├── setup_environment.sh   # Environment setup
│   ├── build_photonsim.sh     # Build script
│   ├── clean_build.sh         # Clean build directory
│   └── check_installation.sh  # Verify installation
└── jobs/                      # Job submission and management
    ├── generate_jobs.sh       # Main job generation script
    ├── monitor_jobs.sh        # Monitor running jobs
    └── cleanup_jobs.sh        # Clean job outputs
```

## Configuration

### user_paths.sh

Copy `user_paths.sh.template` to `user_paths.sh` and configure:

```bash
# Software installations
export GEANT4_INSTALL_DIR="/path/to/geant4/install"
export ROOT_INSTALL_DIR="/path/to/root/install"

# Output paths
export OUTPUT_BASE_PATH="/path/to/photonsim/output"
export LUCID_PATH="/path/to/LUCiD"

# SLURM configuration
export SLURM_PARTITION="shared"
export SLURM_ACCOUNT="neutrino:cider-ml"

# Resource defaults
export DEFAULT_CPUS="1"
export DEFAULT_MEMORY="4g"
export DEFAULT_TIME="02:00:00"
```

On S3DF, you can use existing installations:
```bash
export GEANT4_INSTALL_DIR="/sdf/data/neutrino/cjesus/software/builds/geant4"
export ROOT_INSTALL_DIR="/sdf/data/neutrino/cjesus/software/builds/root"
```

## Job Generation

All job generation uses JSON configuration files in `macros/data_production_config/`.

### generate_jobs.sh

```bash
./jobs/generate_jobs.sh -c <config_json> [-s] [-t]
```

**Options:**
- `-c`: Path to JSON configuration file (required)
- `-s`: Submit jobs to SLURM (default: prepare only)
- `-t`: Test mode - create only one job

### JSON Configuration Format

```json
{
  "config_number": 1,
  "name": "muon_uniform_up_to_1500MeV",
  "description": "Uniform energy muons with LUCiD processing",
  "material": "water",
  "output_path": "uniform_energy",
  "energy_distribution": "uniform",
  "store_individual_photons": true,
  "run_lucid": true,
  "disable_decays": false,
  "particles": [
    {
      "type": "mu-",
      "energy_min_MeV": 210,
      "energy_max_MeV": 1500
    }
  ],
  "lucid_options": {
    "apply_smearing": true,
    "apply_rotation": true,
    "apply_translation": true
  },
  "n_jobs": 100,
  "n_events_per_job": 1000
}
```

### Configuration Fields

| Field                 | Type    | Description                                       |
|-----------------------|---------|---------------------------------------------------|
| `config_number`       | integer | Unique ID (used in output folder: `config_XXXXXX`)|
| `name`                | string  | Human-readable name                               |
| `material`            | string  | "water" (other materials coming soon)             |
| `output_path`         | string  | Subdirectory for output                           |
| `energy_distribution` | string  | "uniform" or "monoenergetic"                      |
| `particles`           | array   | List of particles with energy ranges              |
| `disable_decays`      | boolean | Disable decay processes (for lookup tables)       |
| `lucid_options`       | object  | LUCiD processing flags                            |
| `n_jobs`              | integer | Number of SLURM jobs                              |
| `n_events_per_job`    | integer | Events per job                                    |

### Multi-Particle Events

For events with multiple primaries, specify per-particle energy ranges:

```json
{
  "particles": [
    {"type": "mu-", "energy_min_MeV": 105, "energy_max_MeV": 1500},
    {"type": "pi+", "energy_min_MeV": 122, "energy_max_MeV": 1500}
  ]
}
```

## Output Structure

All data production jobs use a consistent output structure:

```
OUTPUT_BASE_PATH/
└── water/
    └── uniform_energy/
        ├── config_000001/          # mu- single particle
        │   ├── job_000001.mac
        │   ├── run_job_000001.sh
        │   ├── submit_job_000001.sbatch
        │   ├── output_job_000001.root
        │   └── events_job_000001.h5  (if run_lucid: true)
        ├── config_000002/          # pi+ single particle
        └── config_000004/          # mu- + pi+ multi-particle
```

## Job Management

### Monitor Jobs

```bash
./jobs/monitor_jobs.sh [-a] [-w] [-o output_dir]
```

- `-a`: Show all jobs (default: only PhotonSim jobs)
- `-w`: Watch mode - refresh every 30 seconds
- `-o`: Check specific output directory

### Cleanup Jobs

```bash
./jobs/cleanup_jobs.sh -o <output_dir> [-l] [-m] [-s] [-a]
```

- `-l`: Clean log files (*.out, *.err)
- `-m`: Clean macro files (*.mac)
- `-s`: Clean script files (*.sh, *.sbatch)
- `-a`: Clean all temporary files

**Note**: Runs in dry-run mode by default. ROOT and HDF5 files are always preserved.

## Utilities

### Build PhotonSim

```bash
./utils/build_photonsim.sh
```

### Check Installation

```bash
./utils/check_installation.sh
```

### Clean Build

```bash
./utils/clean_build.sh
```

## Example Workflows

### 1. Single Particle Dataset

```bash
# Generate muon dataset with uniform energy 210-1500 MeV
./jobs/generate_jobs.sh -c ../macros/data_production_config/dataprod_single_neg_mu.json -s
```

### 2. Multi-Particle Dataset

```bash
# Generate mu- + pi+ mixed events
./jobs/generate_jobs.sh -c ../macros/data_production_config/dataprod_neg_mu_pos_pion.json -s
```

### 3. Test Before Production

```bash
# Test mode creates only one job
./jobs/generate_jobs.sh -c ../macros/data_production_config/dataprod_single_neg_mu.json -t

# Check the generated files
ls -la $OUTPUT_BASE_PATH/water/uniform_energy/config_000001/

# If looks good, submit all
./jobs/generate_jobs.sh -c ../macros/data_production_config/dataprod_single_neg_mu.json -s
```

## Troubleshooting

### Environment Issues

1. Check `user_paths.sh` configuration
2. Verify GEANT4 and ROOT installations
3. Run `./utils/check_installation.sh`

### Build Failures

1. Clean build: `./utils/clean_build.sh`
2. Check environment: `source ./utils/setup_environment.sh`
3. Rebuild: `./utils/build_photonsim.sh`

### Job Failures

1. Check SLURM logs: `cat config_XXXXXX/job_*-*.out`
2. Check error logs: `cat config_XXXXXX/job_*-*.err`
3. Test locally by running the generated `run_job_*.sh` script
