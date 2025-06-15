# S3DF Scripts for PhotonSim

This directory contains scripts for building, running, and managing PhotonSim jobs on the S3DF cluster at SLAC.

## Quick Start

1. **Configure your paths**:
   ```bash
   cp user_paths.sh.template user_paths.sh
   # Edit user_paths.sh with your specific paths
   ```

2. **Build PhotonSim**:
   ```bash
   ./utils/build_photonsim.sh
   ```

3. **Submit a single job**:
   ```bash
   ./jobs/submit_photonsim_job.sh -p mu- -n 1000 -e 1000 -o /path/to/output
   ```

4. **Submit multiple jobs**:
   ```bash
   ./jobs/submit_photonsim_batch.sh -c jobs/example_batch_config.txt -s
   ```

## Directory Structure

```
s3df_scripts/
├── user_paths.sh              # User-specific configuration (DO NOT COMMIT)
├── utils/                     # Build and environment utilities
│   ├── setup_environment.sh   # Environment setup
│   ├── build_photonsim.sh     # Build script
│   ├── clean_build.sh         # Clean build directory
│   ├── run_photonsim.sh       # Local run script
│   └── check_installation.sh  # Verify installation
├── jobs/                      # Job submission and management
│   ├── submit_photonsim_job.sh    # Submit single job
│   ├── submit_photonsim_batch.sh  # Submit multiple jobs
│   ├── monitor_jobs.sh             # Monitor running jobs
│   ├── cleanup_jobs.sh             # Clean job outputs
│   ├── example_batch_config.txt    # Example configuration
│   └── README.md                   # Job scripts documentation
└── README.md                  # This file
```

## Configuration

### user_paths.sh
This file contains all user-specific paths and should be configured for each user:

```bash
# GEANT4 and ROOT installations
export GEANT4_INSTALL_DIR="/path/to/geant4/build"
export ROOT_INSTALL_DIR="/path/to/root/build"

# PhotonSim output directory
export PHOTONSIM_OUTPUT_BASE="/path/to/output"

# SLURM configuration
export SLURM_PARTITION="shared"
export SLURM_ACCOUNT="your-account"

# Resource defaults
export DEFAULT_CPUS="1"
export DEFAULT_MEMORY="4g"
export DEFAULT_TIME="02:00:00"
```

**Important**: Never commit `user_paths.sh` to git as it contains user-specific paths.

## Utilities (utils/)

### setup_environment.sh
Sets up the environment for building and running PhotonSim:
- Sources GEANT4 and ROOT environments
- Sets up library paths
- Configures environment variables

```bash
source ./utils/setup_environment.sh
```

### build_photonsim.sh
Builds PhotonSim with proper configuration:
- Sources environment automatically
- Configures CMake with correct paths
- Builds with parallel compilation
- Reports build status

```bash
./utils/build_photonsim.sh
```

### check_installation.sh
Verifies that all dependencies are properly installed:
- Checks system tools (cmake, make, g++)
- Verifies GEANT4 and ROOT installations
- Validates PhotonSim source structure

```bash
./utils/check_installation.sh
```

### clean_build.sh
Removes the build directory for fresh compilation:
```bash
./utils/clean_build.sh
```

### run_photonsim.sh
Runs PhotonSim locally with a specified macro:
```bash
./utils/run_photonsim.sh [macro_file]
```

## Job Management (jobs/)

### Single Job Submission
```bash
./jobs/submit_photonsim_job.sh -p <particle> -n <nevents> -e <energy> -o <output_dir> [-f <filename>]
```

Parameters:
- `-p`: Particle type (default: mu-)
- `-n`: Number of events (default: 1000)
- `-e`: Energy in MeV (default: 1000)
- `-o`: Output directory (required)
- `-f`: Output filename (default: output.root)

### Batch Job Submission
```bash
./jobs/submit_photonsim_batch.sh -c <config_file> [-s] [-t]
```

Options:
- `-c`: Configuration file (required)
- `-s`: Submit jobs to SLURM (default: prepare only)
- `-t`: Test mode - create only one job

### Job Monitoring
```bash
./jobs/monitor_jobs.sh [-a] [-w] [-o output_dir]
```

Options:
- `-a`: Show all jobs (default: only PhotonSim jobs)
- `-w`: Watch mode - refresh every 30 seconds
- `-o`: Check specific output directory for results

### Job Cleanup
```bash
./jobs/cleanup_jobs.sh -o <output_dir> [-l] [-m] [-s] [-a]
```

Options:
- `-o`: Output directory to clean (required)
- `-l`: Clean log files (job-*.out, job-*.err)
- `-m`: Clean macro files (*.mac)
- `-s`: Clean script files (*.sh, *.sbatch)
- `-a`: Clean all (logs, macros, and scripts)

**Note**: Runs in dry-run mode by default. ROOT files are always preserved.

## Output Organization

Jobs create outputs following this structure:
```
output_directory/
├── particle_type/
│   ├── energyMeV/
│   │   ├── output.root              # Simulation data
│   │   ├── run_*.mac               # GEANT4 macro
│   │   ├── run_photonsim.sh       # Job execution script
│   │   ├── submit_job.sbatch      # SLURM submission script
│   │   ├── job-*.out              # SLURM output log
│   │   └── job-*.err              # SLURM error log
```

## Example Workflows

### 1. First-time Setup
```bash
# Configure paths
cp user_paths.sh.template user_paths.sh
vim user_paths.sh

# Verify installation
./utils/check_installation.sh

# Build PhotonSim
./utils/build_photonsim.sh
```

### 2. Single Job Test
```bash
# Submit single job
./jobs/submit_photonsim_job.sh -p mu- -n 100 -e 500 -o /path/to/output

# Monitor
./jobs/monitor_jobs.sh -w
```

### 3. Batch Production
```bash
# Create configuration
cat > my_batch.txt << EOF
mu- 1000 500 /path/to/output
mu- 1000 1000 /path/to/output
mu- 1000 2000 /path/to/output
EOF

# Submit all jobs
./jobs/submit_photonsim_batch.sh -c my_batch.txt -s

# Monitor progress
./jobs/monitor_jobs.sh -w -o /path/to/output
```

### 4. Cleanup After Production
```bash
# Remove temporary files, keep ROOT data
./jobs/cleanup_jobs.sh -o /path/to/output -a
```

## SLURM Configuration

Default job settings (configurable in `user_paths.sh`):
- **Partition**: shared
- **Account**: neutrino:cider-ml
- **CPUs**: 1
- **Memory**: 4GB per CPU
- **Time limit**: 2 hours

## Troubleshooting

### Environment Issues
1. Check `user_paths.sh` configuration
2. Verify GEANT4 and ROOT installations
3. Run `./utils/check_installation.sh`

### Build Failures
1. Clean build directory: `./utils/clean_build.sh`
2. Check environment: `source ./utils/setup_environment.sh`
3. Rebuild: `./utils/build_photonsim.sh`

### Job Failures
1. Check SLURM logs: `job-*.out` and `job-*.err`
2. Test locally: run the generated `run_photonsim.sh` script
3. Verify output directory permissions

### Path Resolution
All scripts automatically resolve their locations and find the PhotonSim root directory. No manual path configuration needed in the scripts themselves.

## Notes

- All scripts are designed to work from any directory
- User-specific configuration is centralized in `user_paths.sh`
- Scripts include comprehensive error checking and user feedback
- Dry-run modes are available for testing before execution