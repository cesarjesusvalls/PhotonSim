#!/usr/bin/env python3
"""
Validation script for label-based rotation logic with 500 MeV pions.
Shows photons and tracks before and after rotation.
Creates interactive HTML plots for 3 events.
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

# Configuration
root_file = 'test_2pions.root'
events_to_validate = [0, 1, 2]  # Validate 3 events
n_photons_to_sample = 500
master_seed = 42

print("="*70)
print("PION ROTATION VALIDATION (500 MeV pi-)")
print("="*70)
print()

# Define colors for labels
colors_palette = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow']
category_names = {0: 'Primary', 1: 'DecayElectron', 2: 'SecondaryPion', 3: 'GammaShower'}

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
        color = colors_palette[label_idx % len(colors_palette)]

        print(f"Label {label_idx} ({cat_name}):")
        print(f"  PDG: {track_info['pdg']}")
        print(f"  Energy: {track_info['energy']:.2f} MeV")
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
        label_names.append(f"Label {label_idx} ({cat_name})")

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
        axis_norm = jnp.linalg.norm(rotation_axis)

        rotation_axis = jnp.where(
            axis_norm < 1e-6,
            jnp.array([1.0, 0.0, 0.0]),
            rotation_axis / (axis_norm + 1e-8)
        )

        rotation_angle = jnp.arccos(jnp.clip(jnp.dot(source_norm, target_norm), -1.0, 1.0))
        print(f"  Rotation axis: {rotation_axis}")
        print(f"  Rotation angle: {rotation_angle:.4f} rad ({np.degrees(rotation_angle):.2f} deg)")

        for label_idx in label_indices:
            rotation_per_label[label_idx] = (rotation_axis, rotation_angle)

        print()

    # Apply rotations
    print("AFTER ROTATION:")
    print("-"*70)

    sampled_photons_after = []
    sampled_directions_after = []
    track_positions_after = []
    track_directions_after = []

    for label_idx, label in enumerate(labels):
        track_info = label['track_info']

        if track_info is None or label_idx >= len(sampled_photons_before):
            continue

        photon_origins = sampled_photons_before[label_idx]
        photon_dirs = sampled_directions_before[label_idx]
        track_position = jnp.array(track_positions_before[label_idx])
        track_direction = jnp.array(track_directions_before[label_idx])

        cat_name = category_names.get(track_info['category'], f"Unknown_{track_info['category']}")

        if label_idx in rotation_per_label:
            rotation_axis, rotation_angle = rotation_per_label[label_idx]

            # Rotate photons
            rotated_photon_origins = np.array([
                jax_rotate_vector(jnp.array(p), rotation_axis, rotation_angle)
                for p in photon_origins
            ])
            rotated_photon_dirs = np.array([
                jax_rotate_vector(jnp.array(d), rotation_axis, rotation_angle)
                for d in photon_dirs
            ])

            # Rotate track info
            rotated_track_position = jax_rotate_vector(track_position, rotation_axis, rotation_angle)
            rotated_track_direction = jax_rotate_vector(track_direction, rotation_axis, rotation_angle)

            sampled_photons_after.append(np.array(rotated_photon_origins))
            sampled_directions_after.append(np.array(rotated_photon_dirs))
            track_positions_after.append(np.array(rotated_track_position))
            track_directions_after.append(np.array(rotated_track_direction))

            print(f"Label {label_idx} ({cat_name}):")
            print(f"  Track position: {np.array(rotated_track_position)}")
            print(f"  Track direction: {np.array(rotated_track_direction)}")
            print()
        else:
            # No rotation
            sampled_photons_after.append(photon_origins)
            sampled_directions_after.append(photon_dirs)
            track_positions_after.append(np.array(track_position))
            track_directions_after.append(np.array(track_direction))

            print(f"Label {label_idx} ({cat_name}): No rotation")
            print()

    return {
        'event_idx': event_idx,
        'n_labels': len(sampled_photons_before),
        'sampled_photons_before': sampled_photons_before,
        'track_positions_before': track_positions_before,
        'track_directions_before': track_directions_before,
        'sampled_photons_after': sampled_photons_after,
        'track_positions_after': track_positions_after,
        'track_directions_after': track_directions_after,
        'label_colors': label_colors,
        'label_names': label_names
    }

# Process all events
events_data = []
for event_idx in events_to_validate:
    events_data.append(process_event(event_idx))

# Create interactive plots for each event
print()
print("="*70)
print("CREATING INTERACTIVE VISUALIZATIONS")
print("="*70)

for event_data in events_data:
    event_idx = event_data['event_idx']

    # Create subplots: 1 row, 2 columns (before and after)
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('BEFORE Rotation', 'AFTER Rotation'),
        specs=[[{'type': 'scatter3d'}, {'type': 'scatter3d'}]],
        horizontal_spacing=0.05
    )

    # BEFORE rotation (left plot)
    for i in range(event_data['n_labels']):
        photons = event_data['sampled_photons_before'][i]
        track_pos = event_data['track_positions_before'][i]
        track_dir = event_data['track_directions_before'][i]
        color = event_data['label_colors'][i]
        label_name = event_data['label_names'][i]

        # Plot photons
        fig.add_trace(
            go.Scatter3d(
                x=photons[:, 0], y=photons[:, 1], z=photons[:, 2],
                mode='markers',
                marker=dict(size=2, color=color, opacity=0.3),
                name=label_name,
                legendgroup=f'label{i}',
                showlegend=True
            ),
            row=1, col=1
        )

        # Plot track arrow (skip for GammaShower as direction is not meaningful)
        if 'GammaShower' not in label_name:
            scale = 10  # Arrow length in cm
            fig.add_trace(
                go.Scatter3d(
                    x=[track_pos[0], track_pos[0] + track_dir[0]*scale],
                    y=[track_pos[1], track_pos[1] + track_dir[1]*scale],
                    z=[track_pos[2], track_pos[2] + track_dir[2]*scale],
                    mode='lines+markers',
                    line=dict(color=color, width=12),
                    marker=dict(size=[8, 12], color=color, symbol=['circle', 'diamond']),
                    name=f'{label_name} track',
                    legendgroup=f'label{i}',
                    showlegend=False
                ),
                row=1, col=1
            )

    # AFTER rotation (right plot)
    for i in range(event_data['n_labels']):
        photons = event_data['sampled_photons_after'][i]
        track_pos = event_data['track_positions_after'][i]
        track_dir = event_data['track_directions_after'][i]
        color = event_data['label_colors'][i]
        label_name = event_data['label_names'][i]

        # Plot photons
        fig.add_trace(
            go.Scatter3d(
                x=photons[:, 0], y=photons[:, 1], z=photons[:, 2],
                mode='markers',
                marker=dict(size=2, color=color, opacity=0.3),
                name=label_name,
                legendgroup=f'label{i}',
                showlegend=False
            ),
            row=1, col=2
        )

        # Plot track arrow (skip for GammaShower as direction is not meaningful)
        if 'GammaShower' not in label_name:
            scale = 10  # Arrow length in cm
            fig.add_trace(
                go.Scatter3d(
                    x=[track_pos[0], track_pos[0] + track_dir[0]*scale],
                    y=[track_pos[1], track_pos[1] + track_dir[1]*scale],
                    z=[track_pos[2], track_pos[2] + track_dir[2]*scale],
                    mode='lines+markers',
                    line=dict(color=color, width=12),
                    marker=dict(size=[8, 12], color=color, symbol=['circle', 'diamond']),
                    name=f'{label_name} track',
                    legendgroup=f'label{i}',
                    showlegend=False
                ),
                row=1, col=2
            )

    # Update layout with bigger legend markers and smaller figure
    fig.update_layout(
        title=f'Event {event_idx}: 500 MeV Pion Rotation Validation',
        scene=dict(
            xaxis_title='X (cm)',
            yaxis_title='Y (cm)',
            zaxis_title='Z (cm)',
            aspectmode='data'
        ),
        scene2=dict(
            xaxis_title='X (cm)',
            yaxis_title='Y (cm)',
            zaxis_title='Z (cm)',
            aspectmode='data'
        ),
        legend=dict(
            itemsizing='constant',
            itemwidth=50,
            tracegroupgap=5,
            font=dict(size=12)
        ),
        height=600,
        width=1300
    )

    # Save as HTML
    filename = f'pion_rotation_validation_event{event_idx}.html'
    fig.write_html(filename)
    print(f"✓ Saved event {event_idx} to {filename}")

print()
print("="*70)
print("VALIDATION COMPLETE")
print("="*70)
print(f"\nOpen the HTML files in a browser to interactively explore the 3D plots:")
for event_idx in events_to_validate:
    print(f"  - pion_rotation_validation_event{event_idx}.html")
