#!/usr/bin/env python3
"""
3D Energy Deposit Visualizer for PhotonSim

Interactive 3D visualization tool for energy deposits from PhotonSim.
Shows where energy is deposited in the detector volume for scintillation modeling.

Usage:
    python visualize_energy_deposits.py [root_file]

Requirements:
    - uproot (for ROOT file reading)
    - numpy
    - matplotlib

Author: PhotonSim Project
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import argparse
import sys
try:
    import uproot
except ImportError:
    print("Error: uproot package required. Install with: pip install uproot")
    sys.exit(1)

class EnergyDepositVisualizer:
    """Interactive 3D visualizer for energy deposits."""
    
    def __init__(self, root_file_path):
        """Initialize the visualizer with ROOT file data."""
        self.root_file_path = root_file_path
        self.current_event = 0
        self.data = None
        self.n_events = 0
        self.fig = None
        self.ax = None
        
        # Load data and setup plot
        self.load_data()
        self.setup_plot()
        
    def load_data(self):
        """Load energy deposit data from ROOT file."""
        print(f"Creating PhotonSim energy deposit visualizer for {self.root_file_path}")
        
        try:
            with uproot.open(self.root_file_path) as file:
                tree = file["OpticalPhotons"]
                
                # Load energy deposit data
                self.data = {
                    'EventID': tree['EventID'].array(library='np'),
                    'PrimaryEnergy': tree['PrimaryEnergy'].array(library='np'),
                    'NEnergyDeposits': tree['NEnergyDeposits'].array(library='np'),
                    'EdepPosX': tree['EdepPosX'].array(library='np'),
                    'EdepPosY': tree['EdepPosY'].array(library='np'),
                    'EdepPosZ': tree['EdepPosZ'].array(library='np'),
                    'EdepEnergy': tree['EdepEnergy'].array(library='np'),
                    'EdepTime': tree['EdepTime'].array(library='np'),
                    'EdepParticle': tree['EdepParticle'].array(library='np'),
                    'EdepParentID': tree['EdepParentID'].array(library='np'),
                }
                
                self.n_events = len(self.data['EventID'])
                total_deposits = np.sum(self.data['NEnergyDeposits'])
                avg_primary_energy = np.mean(self.data['PrimaryEnergy'])
                
                print(f"Loaded {self.n_events} events from {self.root_file_path}")
                print(f"Total energy deposits: {total_deposits:,}")
                print(f"Average primary energy: {avg_primary_energy:.1f} MeV")
                
                if total_deposits == 0:
                    print("Warning: No energy deposits found in data!")
                
        except Exception as e:
            print(f"Error loading ROOT file: {e}")
            sys.exit(1)
    
    def setup_plot(self):
        """Setup the 3D matplotlib figure."""
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(12, 9))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Set up the plot aesthetics
        self.ax.set_facecolor('black')
        self.fig.patch.set_facecolor('black')
        
        # Add text for instructions
        self.fig.text(0.02, 0.02, "Controls: ←/→ or P/N = Navigate events, R = Refresh, Mouse = Rotate/Zoom", 
                     color='white', fontsize=10)
    
    def calculate_plot_bounds(self, event_data, padding_factor=1.3):
        """
        Calculate optimal plot bounds based on energy deposit distribution.
        
        Args:
            event_data (dict): Event data containing deposit positions
            padding_factor (float): Factor for padding around deposit cloud
            
        Returns:
            tuple: (x_range, y_range, z_range) as (min, max) tuples
        """
        if len(event_data['pos_x']) == 0:
            # No deposits, use default range around origin
            default_range = 1.0  # 1 meter
            return ((-default_range, default_range), 
                   (-default_range, default_range), 
                   (-default_range, default_range))
        
        # Calculate bounds from deposit positions
        x_min, x_max = np.min(event_data['pos_x']), np.max(event_data['pos_x'])
        y_min, y_max = np.min(event_data['pos_y']), np.max(event_data['pos_y'])
        z_min, z_max = np.min(event_data['pos_z']), np.max(event_data['pos_z'])
        
        # Add padding and ensure we include origin
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        z_center = (z_min + z_max) / 2
        
        x_range = max(abs(x_max - x_center), abs(x_min - x_center)) * padding_factor
        y_range = max(abs(y_max - y_center), abs(y_min - y_center)) * padding_factor
        z_range = max(abs(z_max - z_center), abs(z_min - z_center)) * padding_factor
        
        # Ensure origin is included with adaptive minimum range
        actual_extent = max(x_range, y_range, z_range)
        min_range = max(0.05, actual_extent * 0.1)  # 5cm minimum or 10% of actual extent
        
        x_range = max(x_range, min_range, abs(x_center) + min_range/2)
        y_range = max(y_range, min_range, abs(y_center) + min_range/2)
        z_range = max(z_range, min_range, abs(z_center) + min_range/2)
        
        return ((x_center - x_range, x_center + x_range),
                (y_center - y_range, y_center + y_range),
                (z_center - z_range, z_center + z_range))
    
    def draw_detector_geometry(self, plot_bounds=None):
        """
        Draw the detector volume outline and coordinate axes.
        
        Args:
            plot_bounds (tuple): Optional plot bounds to adjust detector visualization
        """
        # Use plot bounds to draw meaningful volume outline
        if plot_bounds:
            x_range, y_range, z_range = plot_bounds
            x_min, x_max = x_range
            y_min, y_max = y_range  
            z_min, z_max = z_range
        else:
            # Fallback to default range
            default_size = 1.0
            x_min = y_min = z_min = -default_size
            x_max = y_max = z_max = default_size
        
        # Define detector cube vertices using actual bounds
        vertices = np.array([
            [x_min, y_min, z_min], [x_max, y_min, z_min], 
            [x_max, y_max, z_min], [x_min, y_max, z_min],  # bottom face
            [x_min, y_min, z_max], [x_max, y_min, z_max], 
            [x_max, y_max, z_max], [x_min, y_max, z_max]   # top face
        ])
        
        # Define the edges of the cube
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # bottom face
            [4, 5], [5, 6], [6, 7], [7, 4],  # top face
            [0, 4], [1, 5], [2, 6], [3, 7]   # vertical edges
        ]
        
        # Draw the edges
        for edge in edges:
            points = vertices[edge]
            self.ax.plot3D(points[:, 0], points[:, 1], points[:, 2], 
                          color='cyan', alpha=0.3, linewidth=1)
        
    
    def get_event_data(self, event_id):
        """
        Get energy deposit data for a specific event.
        
        Args:
            event_id (int): Event ID to retrieve
            
        Returns:
            dict: Event data including positions, energies, times, particles
        """
        if event_id >= self.n_events:
            return None
            
        return {
            'event_id': self.data['EventID'][event_id],
            'primary_energy': self.data['PrimaryEnergy'][event_id],
            'n_deposits': self.data['NEnergyDeposits'][event_id],
            'pos_x': self.data['EdepPosX'][event_id] / 1000.0,  # Convert mm to m
            'pos_y': self.data['EdepPosY'][event_id] / 1000.0,  # Convert mm to m
            'pos_z': self.data['EdepPosZ'][event_id] / 1000.0,  # Convert mm to m
            'energy': self.data['EdepEnergy'][event_id] * 1000.0,  # Convert MeV to keV
            'time': self.data['EdepTime'][event_id],  # ns
            'particle': self.data['EdepParticle'][event_id],
            'parent_id': self.data['EdepParentID'][event_id],
        }
    
    def plot_event(self, event_id=None):
        """
        Plot energy deposits for a specific event.
        
        Args:
            event_id (int): Event ID to plot. If None, uses current_event.
        """
        if event_id is None:
            event_id = self.current_event
            
        # Clear the plot completely
        self.fig.clear()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor('black')
        
        # Recreate navigation buttons if they were created before
        if hasattr(self, 'buttons_created') and self.buttons_created:
            plt.subplots_adjust(bottom=0.15)
            self._add_navigation_buttons()
        
        # Get event data
        event_data = self.get_event_data(event_id)
        if event_data is None:
            print(f"Event {event_id} not found")
            return
        
        # Calculate optimal plot bounds
        plot_bounds = self.calculate_plot_bounds(event_data)
        
        # Draw detector geometry
        self.draw_detector_geometry(plot_bounds)
        
        # Plot energy deposits
        n_deposits = len(event_data['pos_x'])
        if n_deposits > 0:
            # Performance optimization for large number of deposits
            max_display_deposits = 5000
            if n_deposits > max_display_deposits:
                indices = np.random.choice(n_deposits, max_display_deposits, replace=False)
                pos_x_display = event_data['pos_x'][indices]
                pos_y_display = event_data['pos_y'][indices]
                pos_z_display = event_data['pos_z'][indices]
                energy_display = event_data['energy'][indices]
                time_display = event_data['time'][indices]
                particle_display = [event_data['particle'][i] for i in indices]
                parent_id_display = event_data['parent_id'][indices]
                print(f"Displaying {max_display_deposits:,} of {n_deposits:,} deposits for performance")
            else:
                pos_x_display = event_data['pos_x']
                pos_y_display = event_data['pos_y']
                pos_z_display = event_data['pos_z']
                energy_display = event_data['energy']
                time_display = event_data['time']
                particle_display = event_data['particle']
                parent_id_display = event_data['parent_id']
            
            # Create size array based on energy (log scale for better visibility)
            log_energy = np.log10(np.maximum(energy_display, 0.1))  # Avoid log(0)
            sizes = 10 + 30 * (log_energy - np.min(log_energy)) / (np.max(log_energy) - np.min(log_energy) + 1e-10)
            
            # Color deposits by particle type and primary/secondary
            colors = []
            for i, particle in enumerate(particle_display):
                if parent_id_display[i] == 0:  # Primary
                    if particle == 'mu-':
                        colors.append('red')
                    elif particle == 'e-':
                        colors.append('orange')
                    else:
                        colors.append('yellow')
                else:  # Secondary
                    if particle == 'e-':
                        colors.append('lightblue')
                    elif particle == 'gamma':
                        colors.append('green')
                    else:
                        colors.append('white')
            
            # Plot energy deposits
            scatter = self.ax.scatter(pos_x_display, pos_y_display, pos_z_display,
                                    c=colors, s=sizes, alpha=0.7, edgecolors='black', linewidth=0.5)
            
            # Create custom legend
            legend_elements = []
            from matplotlib.patches import Circle
            legend_elements.append(Circle((0, 0), 0, facecolor='red', label='Primary μ⁻'))
            legend_elements.append(Circle((0, 0), 0, facecolor='orange', label='Primary e⁻'))
            legend_elements.append(Circle((0, 0), 0, facecolor='lightblue', label='Secondary e⁻'))
            legend_elements.append(Circle((0, 0), 0, facecolor='green', label='Secondary γ'))
            self.ax.legend(handles=legend_elements, loc='upper right')
        
        # Plot primary particle origin
        self.ax.scatter([0], [0], [0], color='white', s=200, marker='*', 
                       label='Primary origin', edgecolors='black', linewidth=2)
        
        # Set labels and title
        self.ax.set_xlabel('X [m]', color='white', fontsize=12)
        self.ax.set_ylabel('Y [m]', color='white', fontsize=12)
        self.ax.set_zlabel('Z [m]', color='white', fontsize=12)
        
        # Set plot bounds
        x_range, y_range, z_range = plot_bounds
        self.ax.set_xlim(x_range)
        self.ax.set_ylim(y_range)
        self.ax.set_zlim(z_range)
        
        # Force equal aspect ratio
        self.ax.set_box_aspect([
            x_range[1] - x_range[0],
            y_range[1] - y_range[0], 
            z_range[1] - z_range[0]
        ])
        
        # Title with event information
        if n_deposits > 0:
            total_energy = np.sum(event_data['energy'])
            title = f"Event {event_data['event_id']}: {event_data['primary_energy']:.1f} MeV primary particle\\n"
            title += f"{event_data['n_deposits']:,} energy deposits, {total_energy:.1f} keV total"
        else:
            title = f"Event {event_data['event_id']}: {event_data['primary_energy']:.1f} MeV primary particle\\n"
            title += "No energy deposits"
        
        self.ax.set_title(title, color='white', fontsize=12)
        
        # Set initial view
        self.ax.view_init(elev=20, azim=45)
        
        # Style the plot
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.tick_params(axis='z', colors='white')
        
        # Add energy deposit statistics text
        if n_deposits > 0:
            stats_text = f"Size ∝ log(Energy)\\nTotal: {np.sum(event_data['energy']):.1f} keV\\n"
            stats_text += f"Range: {np.min(event_data['energy']):.3f}-{np.max(event_data['energy']):.1f} keV"
            self.ax.text2D(0.02, 0.98, stats_text, transform=self.ax.transAxes, 
                          color='white', fontsize=10, verticalalignment='top',
                          bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
    
    def show(self):
        """Display the visualization with interactive controls."""
        
        def on_key(event):
            """Handle keyboard events."""
            changed = False
            if event.key == 'right' or event.key == 'n':
                if self.current_event < self.n_events - 1:
                    self.next_event()
                    changed = True
            elif event.key == 'left' or event.key == 'p':
                if self.current_event > 0:
                    self.previous_event()
                    changed = True
            elif event.key == 'r':
                self.plot_event()
                changed = True
            elif event.key.isdigit():
                event_num = int(event.key)
                if 0 <= event_num < self.n_events:
                    self.goto_event(event_num)
                    changed = True
            elif event.key == 'h':
                self.show_help()
            elif event.key == 'y':
                self._reset_view()
                changed = True
            
            if changed:
                self._update_buttons()
                self._update_window_title()
        
        # Connect keyboard events
        self.fig.canvas.mpl_connect('key_press_event', on_key)
        
        # Add navigation buttons if more than one event
        if self.n_events > 1:
            plt.subplots_adjust(bottom=0.15)
            self._add_navigation_buttons()
            self.buttons_created = True
        else:
            self.buttons_created = False
        
        # Plot first event
        self.plot_event(0)
        self._update_window_title()
        
        # Show help and start visualization
        self.show_help()
        plt.show()
    
    def next_event(self):
        """Navigate to the next event."""
        if self.current_event < self.n_events - 1:
            self.current_event += 1
            self.plot_event()
            plt.draw()
    
    def previous_event(self):
        """Navigate to the previous event."""
        if self.current_event > 0:
            self.current_event -= 1
            self.plot_event()
            plt.draw()
    
    def goto_event(self, event_id):
        """Navigate to a specific event."""
        if 0 <= event_id < self.n_events:
            self.current_event = event_id
            self.plot_event()
            plt.draw()
    
    def _add_navigation_buttons(self):
        """Add navigation buttons to the figure."""
        from matplotlib.widgets import Button
        
        # Button positions (left, bottom, width, height)
        ax_prev = plt.axes([0.1, 0.02, 0.1, 0.05])
        ax_next = plt.axes([0.25, 0.02, 0.1, 0.05])
        ax_reset = plt.axes([0.4, 0.02, 0.1, 0.05])
        ax_info = plt.axes([0.7, 0.02, 0.2, 0.05])
        
        self.btn_prev = Button(ax_prev, '← Previous')
        self.btn_next = Button(ax_next, 'Next →')
        self.btn_reset = Button(ax_reset, 'Reset View')
        self.btn_info = Button(ax_info, f'Event {self.current_event + 1}/{self.n_events}')
        
        # Button callbacks
        def on_prev(event):
            if self.current_event > 0:
                self.previous_event()
                self._update_buttons()
                self._update_window_title()
        
        def on_next(event):
            if self.current_event < self.n_events - 1:
                self.next_event()
                self._update_buttons()
                self._update_window_title()
        
        def on_reset(event):
            self._reset_view()
        
        self.btn_prev.on_clicked(on_prev)
        self.btn_next.on_clicked(on_next)
        self.btn_reset.on_clicked(on_reset)
        
        # Style buttons
        self.btn_prev.color = 'lightblue'
        self.btn_next.color = 'lightblue'
        self.btn_reset.color = 'lightgreen'
        self.btn_info.color = 'lightgray'
    
    def _update_buttons(self):
        """Update button states and text."""
        try:
            if hasattr(self, 'btn_info'):
                self.btn_info.label.set_text(f'Event {self.current_event + 1}/{self.n_events}')
                
            # Update button colors based on availability
            if hasattr(self, 'btn_prev'):
                self.btn_prev.color = 'lightblue' if self.current_event > 0 else 'lightgray'
            if hasattr(self, 'btn_next'):
                self.btn_next.color = 'lightblue' if self.current_event < self.n_events - 1 else 'lightgray'
        except:
            # Buttons might not be initialized yet
            pass
    
    def _reset_view(self):
        """Reset the 3D view to standard orientation."""
        self.ax.view_init(elev=20, azim=45)
        self.fig.canvas.draw()
    
    def _update_window_title(self):
        """Update the window title with current event info."""
        if hasattr(self, 'fig') and self.fig:
            event_data = self.get_event_data(self.current_event)
            if event_data:
                title = f"PhotonSim Energy Deposits Event {event_data['event_id']}/{self.n_events-1}: "
                title += f"{event_data['primary_energy']:.1f} MeV, "
                title += f"{event_data['n_deposits']:,} deposits"
                self.fig.canvas.manager.set_window_title(title)
    
    def show_help(self):
        """Display help information."""
        help_text = """
=== PhotonSim Energy Deposit Visualization Controls ===
Arrow keys / N,P : Navigate events
R                : Refresh view
0-9              : Jump to event number
H                : Show this help
Mouse            : Rotate, zoom, pan

Visualization:
• Point size ∝ log(energy deposited)
• Colors: Red=Primary μ⁻, Orange=Primary e⁻, 
         Light Blue=Secondary e⁻, Green=Secondary γ
• White star = Primary particle origin
========================================"""
        print(help_text)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='3D Energy Deposit Visualizer for PhotonSim')
    parser.add_argument('root_file', nargs='?', default='build/optical_photons.root',
                       help='ROOT file containing energy deposit data')
    
    args = parser.parse_args()
    
    try:
        visualizer = EnergyDepositVisualizer(args.root_file)
        visualizer.show()
    except KeyboardInterrupt:
        print("\\nVisualization interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()