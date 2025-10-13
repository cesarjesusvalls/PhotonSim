# PhotonSim S3DF Job Scripts - Unified JSON-Based System

This directory contains a unified script for submitting and managing PhotonSim jobs on the S3DF cluster using JSON configuration files.

## Quick Start

```bash
# Create or edit a JSON configuration file
# See macros/data_production_config/ for examples

# Test with one job (doesn't submit)
./generate_jobs.sh -c ../../macros/data_production_config/your_config.json -t

# Prepare all jobs without submitting
./generate_jobs.sh -c ../../macros/data_production_config/your_config.json

# Prepare and submit all jobs to SLURM
./generate_jobs.sh -c ../../macros/data_production_config/your_config.json -s

# Monitor your jobs
./monitor_jobs.sh -w
```

## Main Script

### generate_jobs.sh

Unified script that handles all PhotonSim job generation from JSON configuration files.

```bash
./generate_jobs.sh -c <config_json> [-s] [-t]
```

**Options:**
- `-c`: Path to JSON configuration file (required)
- `-s`: Submit jobs to SLURM (default: prepare only)
- `-t`: Test mode - create only one job

**Features:**
- Supports all energy distributions (monoenergetic, energy scans, uniform)
- Handles single and multi-particle events
- Optional LUCiD processing pipeline
- Configurable photon storage (averaged vs. individual)
- Maintains backward-compatible directory structure

## JSON Configuration Format

All configurations are defined in JSON files located in `macros/data_production_config/`.

### Required Fields

```json
{
  "config_number": 1,
  "name": "config_name",
  "description": "Description of this dataset",
  "output_base_dir": "/path/to/output",
  "energy_distribution": "monoenergetic" | "uniform",
  "store_individual_photons": true | false,
  "run_lucid": true | false,
  "particles": [...],
  "n_jobs": 100,
  "n_events_per_job": 1000
}
```

### Energy Distribution Options

#### 1. Monoenergetic - Single Energy

```json
{
  "energy_distribution": "monoenergetic",
  "energy_MeV": 1000
}
```

**Output structure:** `output_base_dir/particle/1000MeV/`

#### 2. Monoenergetic - Energy Scan

```json
{
  "energy_distribution": "monoenergetic",
  "energy_scan": {
    "start_MeV": 100,
    "stop_MeV": 2000,
    "step_MeV": 10
  }
}
```

**Output structure:** `output_base_dir/particle/100MeV/`, `output_base_dir/particle/110MeV/`, etc.

#### 3. Uniform Energy Distribution

```json
{
  "energy_distribution": "uniform",
  "energy_min_MeV": 210,
  "energy_max_MeV": 1500
}
```

**Output structure:** `output_base_dir/particle/210_1500MeV_uniform/`

### Particle Configuration

#### Single Particle

```json
{
  "particles": [
    {
      "type": "mu-"
    }
  ]
}
```

For uniform energy, uses global `energy_min_MeV` and `energy_max_MeV`.

#### Multiple Particles (requires LUCiD)

```json
{
  "particles": [
    {
      "type": "mu-",
      "energy_min_MeV": 210,
      "energy_max_MeV": 1500
    },
    {
      "type": "pi-",
      "energy_min_MeV": 300,
      "energy_max_MeV": 1200
    }
  ]
}
```

**Requirements:**
- `energy_distribution` must be `"uniform"`
- `run_lucid` must be `true`
- `lucid_path` must be specified

Per-particle energy ranges override global settings. If not specified, falls back to global `energy_min_MeV`/`energy_max_MeV`.

**Output structure:** `output_base_dir/config_XXXXXX/`

### LUCiD Processing

```json
{
  "run_lucid": true,
  "lucid_path": "/sdf/home/c/cjesus/Dev/LUCiD"
}
```

When enabled:
- Automatically runs LUCiD after PhotonSim
- Generates HDF5 files (`events_jobXXXXXX.h5`)
- Sets up singularity environment with CPU-only JAX

## Example Configurations

All examples are in `macros/data_production_config/`:

### 1. Monoenergetic Energy Scan (Averaged Data)
**File:** `monoenergetic_averaged.json`
```json
{
  "energy_distribution": "monoenergetic",
  "energy_scan": {
    "start_MeV": 100,
    "stop_MeV": 2000,
    "step_MeV": 10
  },
  "store_individual_photons": false,
  "run_lucid": false,
  "n_jobs": 1,
  "n_events_per_job": 10000
}
```
**Use case:** Generating lookup tables with high statistics

### 2. Monoenergetic Single Energy (Averaged Data)
**File:** `monoenergetic_single_energy_averaged.json`
```json
{
  "energy_distribution": "monoenergetic",
  "energy_MeV": 1000,
  "store_individual_photons": false,
  "run_lucid": false
}
```
**Use case:** High-statistics simulation at specific energy

### 3. Monoenergetic Event-by-Event
**File:** `monoenergetic_event_by_event.json`
```json
{
  "energy_distribution": "monoenergetic",
  "energy_MeV": 1050,
  "store_individual_photons": true,
  "run_lucid": false,
  "n_jobs": 100,
  "n_events_per_job": 100
}
```
**Use case:** Individual event analysis at fixed energy

### 4. Uniform Energy (No LUCiD)
**File:** `uniform_single_particle.json`
```json
{
  "energy_distribution": "uniform",
  "energy_min_MeV": 210,
  "energy_max_MeV": 1500,
  "store_individual_photons": true,
  "run_lucid": false
}
```
**Use case:** Energy range sampling with ROOT output only

### 5. Uniform Energy + LUCiD
**File:** `uniform_single_particle_lucid.json`
```json
{
  "energy_distribution": "uniform",
  "energy_min_MeV": 210,
  "energy_max_MeV": 1500,
  "store_individual_photons": true,
  "run_lucid": true,
  "lucid_path": "/sdf/home/c/cjesus/Dev/LUCiD"
}
```
**Use case:** Full pipeline with PhotonSim ROOT and LUCiD HDF5 output

### 6. Multi-Particle + LUCiD
**File:** `multiparticle_uniform_lucid.json`
```json
{
  "energy_distribution": "uniform",
  "particles": [
    {
      "type": "mu-",
      "energy_min_MeV": 210,
      "energy_max_MeV": 1500
    },
    {
      "type": "pi-",
      "energy_min_MeV": 300,
      "energy_max_MeV": 1200
    }
  ],
  "store_individual_photons": true,
  "run_lucid": true
}
```
**Use case:** Multi-particle events with shared vertex

## Directory Structure

The script maintains backward-compatible directory structures:

### Monoenergetic (Single Particle)
```
output_base_dir/
└── mu-/
    ├── 100MeV/
    │   ├── output.root (or output_job001.root for multiple jobs)
    │   ├── run_mu-_100MeV.mac
    │   ├── run_photonsim.sh
    │   ├── submit_job.sbatch
    │   └── job-*.{out,err}
    ├── 110MeV/
    └── ...
```

### Uniform Energy (Single Particle)
```
output_base_dir/
└── mu-/
    └── 210_1500MeV_uniform/
        ├── output_job000001.root
        ├── output_job000002.root
        ├── events_job_000001.h5 (if run_lucid: true)
        ├── events_job_000002.h5
        └── ...
```

### Multi-Particle
```
output_base_dir/
└── config_000001/
    ├── README.md
    ├── particle_0_mu-_job_000001.root
    ├── particle_1_pi-_job_000001.root
    ├── events_job_000001.h5
    └── ...
```

## Workflow Examples

### Example 1: Generate Lookup Table
```bash
# Use monoenergetic energy scan config
./generate_jobs.sh -c ../../macros/data_production_config/monoenergetic_averaged.json -s
```

### Example 2: Event-by-Event Analysis at Fixed Energy
```bash
# Edit the JSON to set your desired energy
vim ../../macros/data_production_config/monoenergetic_event_by_event.json

# Generate and submit 100 jobs
./generate_jobs.sh -c ../../macros/data_production_config/monoenergetic_event_by_event.json -s
```

### Example 3: Uniform Energy + LUCiD Pipeline
```bash
# Test first
./generate_jobs.sh -c ../../macros/data_production_config/uniform_single_particle_lucid.json -t

# Submit all jobs
./generate_jobs.sh -c ../../macros/data_production_config/uniform_single_particle_lucid.json -s
```

### Example 4: Multi-Particle Events
```bash
# Create custom configuration
cat > ../../macros/data_production_config/my_multiparticle.json << EOF
{
  "config_number": 10,
  "name": "my_custom_multiparticle",
  "description": "Custom multi-particle configuration",
  "output_base_dir": "/sdf/data/neutrino/cjesus/photonsim_output/water/uniform_energy/multiparticle",
  "energy_distribution": "uniform",
  "store_individual_photons": true,
  "run_lucid": true,
  "lucid_path": "/sdf/home/c/cjesus/Dev/LUCiD",
  "particles": [
    {"type": "mu-", "energy_min_MeV": 200, "energy_max_MeV": 1000},
    {"type": "e-", "energy_min_MeV": 100, "energy_max_MeV": 500}
  ],
  "n_jobs": 50,
  "n_events_per_job": 500
}
EOF

# Generate and submit
./generate_jobs.sh -c ../../macros/data_production_config/my_multiparticle.json -s
```

## Job Management Scripts

### monitor_jobs.sh
Monitor running PhotonSim jobs.

```bash
./monitor_jobs.sh [-a] [-w] [-o output_dir]
```

Options:
- `-a`: Show all jobs (default: only PhotonSim/multiparticle jobs)
- `-w`: Watch mode - refresh every 30 seconds
- `-o`: Check specific output directory for results

Example:
```bash
# Watch mode with output directory
./monitor_jobs.sh -w -o /sdf/data/neutrino/cjesus/photonsim_output/water
```

### cleanup_jobs.sh
Clean up job-related files while preserving ROOT and HDF5 output files.

```bash
./cleanup_jobs.sh -o <output_dir> [-l] [-m] [-s] [-a]
```

Options:
- `-o`: Output directory to clean (required)
- `-l`: Clean log files (job-*.out, job-*.err)
- `-m`: Clean macro files (*.mac)
- `-s`: Clean script files (*.sh, *.sbatch)
- `-a`: Clean all (logs, macros, and scripts)

**Note:** Runs in dry-run mode by default. Edit script to set `DRY_RUN=false`.

## Physics Configuration

All jobs automatically disable decay processes:
- **Muons (mu-, mu+)**: Process 1 (Decay), Process 7 (muMinusCaptureAtRest for mu-)
- **Pions (pi+, pi-)**: Process 1 (Decay)

## SLURM Configuration

Default settings (configured in `../user_paths.sh`):
- Partition: `shared`
- Account: `neutrino:cider-ml`
- CPUs: 1
- Memory: 4GB per CPU
- Time limit: 2 hours

## Migration from Old Scripts

The new unified system replaces these legacy scripts:
- `submit_photonsim_job.sh` → Use JSON with `energy_distribution: "monoenergetic"`, `energy_MeV: X`, `store_individual_photons: false`
- `submit_photonsim_batch.sh` → Use JSON with energy scan
- `submit_photonsim_job_individual.sh` → Use JSON with `store_individual_photons: true`
- `submit_photonsim_batch_individual.sh` → Use JSON with multiple jobs
- `submit_photonsim_job_uniform.sh` → Use JSON with `energy_distribution: "uniform"`
- `submit_photonsim_batch_uniform.sh` → Use JSON with uniform energy
- `submit_photonsim_lucid_job_uniform.sh` → Use JSON with `run_lucid: true`
- `submit_photonsim_lucid_batch_uniform.sh` → Use JSON with uniform + LUCiD
- `generate_dataset.sh` → Use JSON for multi-particle configs

**Legacy scripts are still available but deprecated.**

## Quick Reference Table

| Use Case | Energy Mode | Individual Photons | LUCiD | Example Config |
|----------|-------------|-------------------|-------|----------------|
| Lookup tables | Monoenergetic scan | No | No | `monoenergetic_averaged.json` |
| Single energy, high stats | Monoenergetic | No | No | `monoenergetic_single_energy_averaged.json` |
| Event analysis, fixed E | Monoenergetic | Yes | No | `monoenergetic_event_by_event.json` |
| Energy range, ROOT only | Uniform | Yes | No | `uniform_single_particle.json` |
| Energy range + LUCiD | Uniform | Yes | Yes | `uniform_single_particle_lucid.json` |
| Multi-particle events | Uniform | Yes | Yes | `multiparticle_uniform_lucid.json` |

## Tips

1. **Start with test mode** (`-t`) to verify your configuration before submitting all jobs
2. **Use unique config_number** for each configuration to avoid directory conflicts
3. **Check disk space** before large batch submissions
4. **Monitor job progress** with `monitor_jobs.sh -w`
5. **Clean up** completed job logs with `cleanup_jobs.sh` after verification
