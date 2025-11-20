#!/usr/bin/env python3
"""
Generic validation script for PhotonSim label-based rotation logic.
Shows photons and tracks before and after rotation.
Creates interactive HTML plots for visual inspection.

Works with any particle type and any number of primaries.
"""
import sys
sys.path.append('/Users/cjesus/Software/LUCiD')

import numpy as np
import jax
import jax.numpy as jnp
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from tools.generate import read_label_data_from_photonsim
from tools.simulation import jax_rotate_vector
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Validate PhotonSim rotation with label classification')
parser.add_argument('root_file', type=str, help='Input ROOT file from PhotonSim')
parser.add_argument('--events', type=int, nargs='+', default=[0, 1, 2], help='Event indices to validate (default: 0 1 2)')
parser.add_argument('--photons', type=int, default=500, help='Number of photons to sample per label (default: 500)')
parser.add_argument('--seed', type=int, default=42, help='Random seed for photon sampling (default: 42)')
args = parser.parse_args()

root_file = args.root_file
events_to_validate = args.events
n_photons_to_sample = args.photons
master_seed = args.seed

print("="*70)
print("PHOTONSIM ROTATION VALIDATION")
print("="*70)
print(f"Input file: {root_file}")
print(f"Events to validate: {events_to_validate}")
print(f"Photons to sample per label: {n_photons_to_sample}")
print()

# Define colors for labels
colors_palette = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow',
                  'brown', 'pink', 'olive', 'navy', 'teal', 'maroon']
category_names = {0: 'Primary', 1: 'DecayElectron', 2: 'SecondaryPion', 3: 'GammaShower'}

# PDG code to particle name mapping
pdg_to_name = {
    -211: 'pi-',
    211: 'pi+',
    111: 'pi0',
    -13: 'mu+',
    13: 'mu-',
    -11: 'e+',
    11: 'e-',
    22: 'gamma',
    2212: 'proton',
    2112: 'neutron',
    -2212: 'antiproton',
}

def process_event(event_idx):
    """Process a single event and return data for plotting"""
    print(f"\n{'='*70}")
    print(f"EVENT {event_idx}")
    print(f"{'='*70}")

    # Read label data
    label_data = read_label_data_from_photonsim(root_file, event_idx)

    n_labels = label_data['n_labels']
    labels = label_data['labels']
    all_photon_origins = label_data['photon_origins']
    all_photon_directions = label_data['photon_directions']

    print(f"Event has {n_labels} labels")
    print()

    # Sample photons for each label
    sampled_photons_before = []
    sampled_directions_before = []
    track_positions_before = []
    track_directions_before = []
    label_colors = []
    label_names = []

    print("BEFORE ROTATION:")
    print("-"*70)
    for label_idx, label in enumerate(labels):
        photon_indices = label['photon_indices']
        track_info = label['track_info']

        if track_info is None:
            continue

        cat_name = category_names.get(track_info['category'], f"Unknown_{track_info['category']}")
        particle_name = pdg_to_name.get(track_info['pdg'], f"PDG{track_info['pdg']}")
        color = colors_palette[label_idx % len(colors_palette)]
        kinetic_energy = track_info['energy']

        print(f"Label {label_idx} ({cat_name}):")
        print(f"  Particle: {particle_name} (PDG: {track_info['pdg']})")
        print(f"  Kinetic Energy: {kinetic_energy:.2f} MeV")
        print(f"  Color: {color}")
        print(f"  Track position: {track_info['position']}")
        print(f"  Track direction: {track_info['direction']}")
        print(f"  Total photons: {len(photon_indices)}")

        if len(photon_indices) == 0:
            print(f"  WARNING: No photons for this label")
            print()
            continue

        # Sample photons
        photon_indices_array = np.array(photon_indices, dtype=np.int32)
        n_to_sample = min(n_photons_to_sample, len(photon_indices))
        np.random.seed(master_seed + label_idx + event_idx * 100)
        sampled_indices = np.random.choice(len(photon_indices), size=n_to_sample, replace=False)
        selected_photon_indices = photon_indices_array[sampled_indices]

        photon_origins = all_photon_origins[selected_photon_indices]
        photon_dirs = all_photon_directions[selected_photon_indices]

        sampled_photons_before.append(photon_origins)
        sampled_directions_before.append(photon_dirs)
        track_positions_before.append(track_info['position'])
        track_directions_before.append(track_info['direction'])
        label_colors.append(color)
        label_names.append(f"Label {label_idx} ({cat_name} - {particle_name}, {kinetic_energy:.1f} MeV)")

        print(f"  Sampled {n_to_sample} photons")
        print()

    print()

    # Generate rotations per primary group
    print("GENERATING ROTATIONS PER PRIMARY:")
    print("-"*70)

    # Group labels by primary
    primary_groups = {}
    for label_idx, label in enumerate(labels):
        genealogy = label['genealogy']
        if len(genealogy) > 0:
            primary_track_id = genealogy[0]
            if primary_track_id not in primary_groups:
                primary_groups[primary_track_id] = []
            primary_groups[primary_track_id].append(label_idx)

    rotation_per_label = {}
    master_key = jax.random.PRNGKey(master_seed + event_idx * 1000)

    for primary_track_id, label_indices in primary_groups.items():
        print(f"Primary Track ID {primary_track_id}: Labels {label_indices}")

        # Get primary's true direction
        primary_track_info = label_data['track_info_dict'].get(primary_track_id)
        if primary_track_info is not None:
            source_direction = jnp.array(primary_track_info['direction'])
            print(f"  Source direction: {source_direction}")
        else:
            source_direction = jnp.array([0.0, 0.0, 1.0])
            print(f"  Source direction (fallback): {source_direction}")

        # Generate random target direction
        rotation_key, master_key = jax.random.split(master_key)
        random_values = jax.random.uniform(rotation_key, shape=(2,))
        cos_theta = 2.0 * random_values[0] - 1.0
        phi = 2.0 * jnp.pi * random_values[1]
        sin_theta = jnp.sqrt(1.0 - cos_theta**2)

        target_direction = jnp.array([
            sin_theta * jnp.cos(phi),
            sin_theta * jnp.sin(phi),
            cos_theta
        ])
        print(f"  Target direction: {target_direction}")

        # Calculate rotation
        source_norm = source_direction / (jnp.linalg.norm(source_direction) + 1e-8)
        target_norm = target_direction / (jnp.linalg.norm(target_direction) + 1e-8)

        rotation_axis = jnp.cross(source_norm, target_norm)
        rotation_axis_norm = jnp.linalg.norm(rotation_axis)

        if rotation_axis_norm < 1e-6:
            dot_product = jnp.dot(source_norm, target_norm)
            if dot_product > 0:
                rotation_matrix = jnp.eye(3)
            else:
                perpendicular = jnp.array([1.0, 0.0, 0.0]) if abs(source_norm[0]) < 0.9 else jnp.array([0.0, 1.0, 0.0])
                perpendicular = perpendicular - jnp.dot(perpendicular, source_norm) * source_norm
                perpendicular = perpendicular / jnp.linalg.norm(perpendicular)
                rotation_matrix = 2.0 * jnp.outer(perpendicular, perpendicular) - jnp.eye(3)
        else:
            rotation_axis = rotation_axis / rotation_axis_norm
            cos_angle = jnp.dot(source_norm, target_norm)
            angle = jnp.arccos(jnp.clip(cos_angle, -1.0, 1.0))

            K = jnp.array([
                [0, -rotation_axis[2], rotation_axis[1]],
                [rotation_axis[2], 0, -rotation_axis[0]],
                [-rotation_axis[1], rotation_axis[0], 0]
            ])
            rotation_matrix = jnp.eye(3) + jnp.sin(angle) * K + (1 - jnp.cos(angle)) * (K @ K)

        for label_idx in label_indices:
            rotation_per_label[label_idx] = rotation_matrix

        print()

    # Apply rotations
    print("AFTER ROTATION:")
    print("-"*70)
    sampled_photons_after = []
    sampled_directions_after = []
    track_positions_after = []
    track_directions_after = []

    for i, label_idx in enumerate(range(len(sampled_photons_before))):
        if label_idx not in rotation_per_label:
            print(f"WARNING: No rotation for label {label_idx}")
            sampled_photons_after.append(sampled_photons_before[i])
            sampled_directions_after.append(sampled_directions_before[i])
            track_positions_after.append(track_positions_before[i])
            track_directions_after.append(track_directions_before[i])
            continue

        rotation_matrix = rotation_per_label[label_idx]

        # Rotate photons (positions and directions)
        photons_before = jnp.array(sampled_photons_before[i])
        directions_before = jnp.array(sampled_directions_before[i])

        photons_after = jax.vmap(lambda v: rotation_matrix @ v)(photons_before)
        directions_after = jax.vmap(lambda v: rotation_matrix @ v)(directions_before)

        # Rotate track
        track_pos_before = jnp.array(track_positions_before[i])
        track_dir_before = jnp.array(track_directions_before[i])

        track_pos_after = rotation_matrix @ track_pos_before
        track_dir_after = rotation_matrix @ track_dir_before

        sampled_photons_after.append(np.array(photons_after))
        sampled_directions_after.append(np.array(directions_after))
        track_positions_after.append(np.array(track_pos_after))
        track_directions_after.append(np.array(track_dir_after))

        print(f"Label {label_idx}:")
        print(f"  Track position after: {track_pos_after}")
        print(f"  Track direction after: {track_dir_after}")
        print()

    print()

    return {
        'event_idx': event_idx,
        'n_labels': len(sampled_photons_before),
        'photons_before': sampled_photons_before,
        'photons_after': sampled_photons_after,
        'directions_before': sampled_directions_before,
        'directions_after': sampled_directions_after,
        'track_positions_before': track_positions_before,
        'track_positions_after': track_positions_after,
        'track_directions_before': track_directions_before,
        'track_directions_after': track_directions_after,
        'label_colors': label_colors,
        'label_names': label_names
    }

# Process all events
events_data = []
for event_idx in events_to_validate:
    try:
        event_data = process_event(event_idx)
        if event_data is not None:
            events_data.append(event_data)
    except Exception as e:
        print(f"ERROR processing event {event_idx}: {e}")
        import traceback
        traceback.print_exc()
        continue

# Create interactive plots for all events
print()
print("="*70)
print("CREATING INTERACTIVE VISUALIZATIONS")
print("="*70)

events_to_plot = events_data
print(f"Creating plots for {len(events_to_plot)} events")
print()

for event_data in events_to_plot:
    event_idx = event_data['event_idx']

    # Create side-by-side subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Before Rotation', 'After Rotation'),
        specs=[[{'type': 'scatter3d'}, {'type': 'scatter3d'}]]
    )

    # Plot each label in both before/after
    for i in range(event_data['n_labels']):
        photons_before = event_data['photons_before'][i]
        photons_after = event_data['photons_after'][i]
        track_pos_before = event_data['track_positions_before'][i]
        track_pos_after = event_data['track_positions_after'][i]
        track_dir_before = event_data['track_directions_before'][i]
        track_dir_after = event_data['track_directions_after'][i]
        color = event_data['label_colors'][i]
        label_name = event_data['label_names'][i]

        # Before rotation (left panel)
        fig.add_trace(
            go.Scatter3d(
                x=photons_before[:, 0], y=photons_before[:, 1], z=photons_before[:, 2],
                mode='markers',
                marker=dict(size=2, color=color, opacity=0.3),
                name=label_name,
                legendgroup=f'label{i}',
                showlegend=True
            ),
            row=1, col=1
        )

        # After rotation (right panel)
        fig.add_trace(
            go.Scatter3d(
                x=photons_after[:, 0], y=photons_after[:, 1], z=photons_after[:, 2],
                mode='markers',
                marker=dict(size=2, color=color, opacity=0.3),
                name=label_name,
                legendgroup=f'label{i}',
                showlegend=False
            ),
            row=1, col=2
        )

        # Track arrows (before)
        scale = 5
        fig.add_trace(
            go.Scatter3d(
                x=[track_pos_before[0], track_pos_before[0] + track_dir_before[0]*scale],
                y=[track_pos_before[1], track_pos_before[1] + track_dir_before[1]*scale],
                z=[track_pos_before[2], track_pos_before[2] + track_dir_before[2]*scale],
                mode='lines',
                line=dict(color=color, width=8),
                showlegend=False
            ),
            row=1, col=1
        )

        # Track arrows (after)
        fig.add_trace(
            go.Scatter3d(
                x=[track_pos_after[0], track_pos_after[0] + track_dir_after[0]*scale],
                y=[track_pos_after[1], track_pos_after[1] + track_dir_after[1]*scale],
                z=[track_pos_after[2], track_pos_after[2] + track_dir_after[2]*scale],
                mode='lines',
                line=dict(color=color, width=8),
                showlegend=False
            ),
            row=1, col=2
        )

    # Update layout
    fig.update_layout(
        title=f'Event {event_idx}: Rotation Validation',
        height=700,
        width=1600,
        legend=dict(
            itemsizing='constant',
            itemwidth=50,
            font=dict(size=10)
        )
    )

    # Update scene axes
    fig.update_scenes(
        xaxis_title='X (cm)',
        yaxis_title='Y (cm)',
        zaxis_title='Z (cm)',
        aspectmode='data'
    )

    # Save as HTML
    filename = f'photonsim_rotation_event{event_idx}.html'
    fig.write_html(filename)
    print(f"✓ Saved event {event_idx} to {filename}")

print()
print("="*70)
print("VALIDATION COMPLETE")
print("="*70)
print(f"\nGenerated {len(events_to_plot)} HTML files")
print("Open the HTML files in a browser to interactively explore the 3D plots")
