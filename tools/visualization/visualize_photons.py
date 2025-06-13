#!/usr/bin/env python3
"""
PhotonSim Data Visualizer

Interactive 3D visualization tool for optical photon data from PhotonSim.
Displays photons in 3D space with detector geometry and allows navigation
between events.

Usage:
    python visualize_photons.py [root_file]

Requirements:
    - uproot (for ROOT file reading)
    - numpy
    - matplotlib
    - ipywidgets (for interactive controls)

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

def _check_jupyter_environment():
    """Check if running in a Jupyter environment."""
    try:
        from ipywidgets import interact, IntSlider, Button, VBox, HBox, Output
        from IPython.display import display, clear_output
        # Check if we're actually in Jupyter/IPython
        from IPython import get_ipython
        if get_ipython() is not None:
            return True
        else:
            return False
    except ImportError:
        return False

JUPYTER_AVAILABLE = _check_jupyter_environment()
if not JUPYTER_AVAILABLE:
    # Silent fallback to matplotlib interface
    pass


class PhotonSimVisualizer:
    """Interactive 3D visualizer for PhotonSim optical photon data."""
    
    def __init__(self, root_file_path):
        """
        Initialize the visualizer with ROOT file data.
        
        Args:
            root_file_path (str): Path to the ROOT file containing optical photon data
        """
        self.root_file_path = root_file_path
        self.data = None
        self.current_event = 0
        self.n_events = 0
        self.detector_size = 5.0  # Default 5m detector (will be updated from data)
        self.colorbar = None  # Track current colorbar
        
        # Load data
        self.load_data()
        
        # Setup plot
        self.fig = None
        self.ax = None
        self.setup_plot()
    
    def load_data(self):
        """Load optical photon data from ROOT file."""
        try:
            with uproot.open(self.root_file_path) as file:
                tree = file["OpticalPhotons"]
                
                # Load all data arrays
                self.data = {
                    'EventID': tree['EventID'].array(library='np'),
                    'PrimaryEnergy': tree['PrimaryEnergy'].array(library='np'),
                    'NOpticalPhotons': tree['NOpticalPhotons'].array(library='np'),
                    'PhotonPosX': tree['PhotonPosX'].array(library='np'),
                    'PhotonPosY': tree['PhotonPosY'].array(library='np'),
                    'PhotonPosZ': tree['PhotonPosZ'].array(library='np'),
                    'PhotonDirX': tree['PhotonDirX'].array(library='np'),
                    'PhotonDirY': tree['PhotonDirY'].array(library='np'),
                    'PhotonDirZ': tree['PhotonDirZ'].array(library='np'),
                    'PhotonTime': tree['PhotonTime'].array(library='np'),
                }
                
                self.n_events = len(self.data['EventID'])
                print(f"Loaded {self.n_events} events from {self.root_file_path}")
                
                # Print summary statistics
                total_photons = np.sum(self.data['NOpticalPhotons'])
                avg_energy = np.mean(self.data['PrimaryEnergy'])
                print(f"Total optical photons: {total_photons:,}")
                print(f"Average primary energy: {avg_energy:.1f} MeV")
                
                # Estimate detector size from photon positions
                if self.n_events > 0:
                    all_x = np.concatenate(self.data['PhotonPosX'])
                    all_y = np.concatenate(self.data['PhotonPosY'])
                    all_z = np.concatenate(self.data['PhotonPosZ'])
                    
                    # Convert from mm to m and find detector bounds
                    max_extent = max(np.max(np.abs(all_x)), np.max(np.abs(all_y)), np.max(np.abs(all_z)))
                    self.detector_size = max_extent / 1000.0  # Convert mm to m
                    print(f"Estimated detector size: ±{self.detector_size:.1f} m")
                
        except Exception as e:
            print(f"Error loading ROOT file: {e}")
            sys.exit(1)
    
    def setup_plot(self):
        """Setup the 3D matplotlib figure."""
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Set up the plot aesthetics
        self.ax.set_facecolor('black')
        self.fig.patch.set_facecolor('black')
        
        # Add text for instructions
        self.fig.text(0.02, 0.02, "Controls: ←/→ or P/N = Navigate events, R = Refresh, Mouse = Rotate/Zoom", 
                     color='white', fontsize=10)
    
    def calculate_plot_bounds(self, event_data, padding_factor=1.2):
        """
        Calculate optimal plot bounds based on photon distribution.
        
        Args:
            event_data (dict): Event data containing photon positions
            padding_factor (float): Factor for padding around photon cloud
            
        Returns:
            tuple: (x_range, y_range, z_range) as (min, max) tuples
        """
        if len(event_data['pos_x']) == 0:
            # No photons, use default range around origin
            default_range = 10.0  # 10 meters
            return ((-default_range, default_range), 
                   (-default_range, default_range), 
                   (-default_range, default_range))
        
        # Calculate bounds from photon positions
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
        
        # Ensure origin is included with some minimum range
        min_range = 5.0  # 5 meters minimum
        x_range = max(x_range, min_range, abs(x_center) + min_range)
        y_range = max(y_range, min_range, abs(y_center) + min_range)
        z_range = max(z_range, min_range, abs(z_center) + min_range)
        
        return ((x_center - x_range, x_center + x_range),
                (y_center - y_range, y_center + y_range),
                (z_center - z_range, z_center + z_range))
    
    def draw_detector_geometry(self, plot_bounds=None):
        """
        Draw the detector volume outline.
        
        Args:
            plot_bounds (tuple): Optional plot bounds to adjust detector visualization
        """
        # Use detector size or plot bounds for detector outline
        if plot_bounds:
            x_range, y_range, z_range = plot_bounds
            # Draw a subset of the detector that's visible in the plot
            x_size = min(self.detector_size, (x_range[1] - x_range[0]) / 2)
            y_size = min(self.detector_size, (y_range[1] - y_range[0]) / 2)
            z_size = min(self.detector_size, (z_range[1] - z_range[0]) / 2)
        else:
            x_size = y_size = z_size = self.detector_size
        
        # Define detector cube vertices
        vertices = np.array([
            [-x_size, -y_size, -z_size], [x_size, -y_size, -z_size], 
            [x_size, y_size, -z_size], [-x_size, y_size, -z_size],  # bottom face
            [-x_size, -y_size, z_size], [x_size, -y_size, z_size], 
            [x_size, y_size, z_size], [-x_size, y_size, z_size]      # top face
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
                          color='cyan', alpha=0.4, linewidth=1)
        
        # Add coordinate axes at origin
        axis_length = min(x_size, y_size, z_size) * 0.3
        # X-axis (red)
        self.ax.plot3D([0, axis_length], [0, 0], [0, 0], color='red', linewidth=3, alpha=0.8)
        # Y-axis (green)  
        self.ax.plot3D([0, 0], [0, axis_length], [0, 0], color='green', linewidth=3, alpha=0.8)
        # Z-axis (blue)
        self.ax.plot3D([0, 0], [0, 0], [0, axis_length], color='blue', linewidth=3, alpha=0.8)
    
    def get_event_data(self, event_id):
        """
        Get photon data for a specific event.
        
        Args:
            event_id (int): Event ID to retrieve
            
        Returns:
            dict: Event data including positions, directions, times
        """
        if event_id >= self.n_events:
            return None
            
        return {
            'event_id': self.data['EventID'][event_id],
            'primary_energy': self.data['PrimaryEnergy'][event_id],
            'n_photons': self.data['NOpticalPhotons'][event_id],
            'pos_x': self.data['PhotonPosX'][event_id] / 1000.0,  # Convert mm to m
            'pos_y': self.data['PhotonPosY'][event_id] / 1000.0,  # Convert mm to m
            'pos_z': self.data['PhotonPosZ'][event_id] / 1000.0,  # Convert mm to m
            'dir_x': self.data['PhotonDirX'][event_id],
            'dir_y': self.data['PhotonDirY'][event_id],
            'dir_z': self.data['PhotonDirZ'][event_id],
            'time': self.data['PhotonTime'][event_id],  # ns
        }
    
    def plot_event(self, event_id=None):
        """
        Plot optical photons for a specific event.
        
        Args:
            event_id (int): Event ID to plot. If None, uses current_event.
        """
        if event_id is None:
            event_id = self.current_event
            
        # Clear the plot completely and recreate axes to avoid colorbar layout issues
        self.fig.clear()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor('black')
        self.colorbar = None
        
        # Recreate navigation buttons if we're in matplotlib interface mode
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
        
        # Draw detector geometry with smart sizing
        self.draw_detector_geometry(plot_bounds)
        
        # Plot photon positions (with performance optimization)
        n_photons = len(event_data['pos_x'])
        if n_photons > 0:
            # Sample photons for performance if there are too many
            max_display_photons = 10000  # Limit for smooth interaction
            if n_photons > max_display_photons:
                indices = np.random.choice(n_photons, max_display_photons, replace=False)
                pos_x_display = event_data['pos_x'][indices]
                pos_y_display = event_data['pos_y'][indices]
                pos_z_display = event_data['pos_z'][indices]
                times_display = event_data['time'][indices]
                print(f"Displaying {max_display_photons:,} of {n_photons:,} photons for performance")
            else:
                pos_x_display = event_data['pos_x']
                pos_y_display = event_data['pos_y']
                pos_z_display = event_data['pos_z']
                times_display = event_data['time']
            
            # Color photons by creation time
            if np.max(times_display) > 0:
                # Use actual times for color mapping (not normalized)
                scatter = self.ax.scatter(pos_x_display, pos_y_display, pos_z_display,
                                        c=times_display, s=1, alpha=0.6, cmap='plasma')
            else:
                # All times are zero, use uniform color
                scatter = self.ax.scatter(pos_x_display, pos_y_display, pos_z_display,
                                        c='yellow', s=1, alpha=0.6)
            
            # Add some photon direction vectors (sample to avoid overcrowding)
            n_arrows = min(200, len(pos_x_display))  # Limit number of arrows
            if n_arrows > 0:
                arrow_indices = np.random.choice(len(pos_x_display), n_arrows, replace=False)
                
                # Scale arrows based on plot bounds
                x_range, y_range, z_range = plot_bounds
                plot_scale = min(x_range[1] - x_range[0], y_range[1] - y_range[0], z_range[1] - z_range[0])
                arrow_scale = plot_scale * 0.05  # Arrow length as 5% of plot scale
                
                for i in arrow_indices:
                    self.ax.quiver(pos_x_display[i], pos_y_display[i], pos_z_display[i],
                                  event_data['dir_x'][i] * arrow_scale,
                                  event_data['dir_y'][i] * arrow_scale,
                                  event_data['dir_z'][i] * arrow_scale,
                                  color='white', alpha=0.4, arrow_length_ratio=0.1)
        
        # Plot primary particle origin
        self.ax.scatter([0], [0], [0], color='red', s=100, marker='*', 
                       label='Primary particle origin')
        
        # Set labels and title
        self.ax.set_xlabel('X [m]', color='white', fontsize=12)
        self.ax.set_ylabel('Y [m]', color='white', fontsize=12)
        self.ax.set_zlabel('Z [m]', color='white', fontsize=12)
        
        # Set proportional aspect ratio using smart bounds
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
        title = f"Event {event_data['event_id']}: {event_data['primary_energy']:.1f} MeV primary particle\n"
        title += f"{event_data['n_photons']:,} Cherenkov photons"
        self.ax.set_title(title, color='white', fontsize=12)
        
        # Add colorbar for time
        if n_photons > 0 and np.max(times_display) > 0:
            self.colorbar = plt.colorbar(scatter, ax=self.ax, shrink=0.6, aspect=20)
            self.colorbar.set_label('Creation Time [ns]', color='white')
            self.colorbar.ax.yaxis.set_tick_params(color='white')
            self.colorbar.ax.yaxis.label.set_color('white')
        
        # Constrain view to keep Y-axis vertical
        self.ax.view_init(elev=15, azim=45)  # Set initial view
        
        # Lock the up vector to keep Y vertical during rotation
        self.ax.zaxis.set_rotate_label(False)
        
        # Style the plot
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.tick_params(axis='z', colors='white')
    
    def next_event(self):
        """Navigate to the next event."""
        if self.current_event < self.n_events - 1:
            self.current_event += 1
            self.plot_event()
            self._update_buttons()
            plt.draw()
    
    def previous_event(self):
        """Navigate to the previous event."""
        if self.current_event > 0:
            self.current_event -= 1
            self.plot_event()
            self._update_buttons()
            plt.draw()
    
    def goto_event(self, event_id):
        """
        Navigate to a specific event.
        
        Args:
            event_id (int): Event ID to navigate to
        """
        if 0 <= event_id < self.n_events:
            self.current_event = event_id
            self.plot_event()
            self._update_buttons()
            plt.draw()
    
    def create_interactive_plot(self):
        """Create interactive plot with navigation controls."""
        if JUPYTER_AVAILABLE:
            self._create_jupyter_interface()
        else:
            self._create_matplotlib_interface()
    
    def _create_matplotlib_interface(self):
        """Create matplotlib-based interface with keyboard controls and navigation buttons."""
        
        # Store reference to whether buttons have been created
        self.buttons_created = False
        
        # Main 3D plot takes most of the space
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor('black')
        
        # Adjust layout to make room for buttons
        plt.subplots_adjust(bottom=0.15)
        
        # Add navigation buttons
        self._add_navigation_buttons()
        self.buttons_created = True
        
        def on_key(event):
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
                self.plot_event()  # Refresh
                changed = True
            elif event.key.isdigit():
                # Jump to specific event by number
                event_num = int(event.key)
                if 0 <= event_num < self.n_events:
                    self.goto_event(event_num)
                    changed = True
            elif event.key == 'h':
                # Show help
                self._show_help()
            elif event.key == 'y':
                # Reset view to keep Y vertical
                self._reset_view()
                changed = True
            
            if changed:
                self._update_window_title()
        
        # Mouse motion callback to constrain rotation
        def on_motion(event):
            if event.inaxes == self.ax:
                # Get current view angles
                elev = self.ax.elev
                azim = self.ax.azim
                
                # Constrain elevation to reasonable range to keep Y somewhat vertical
                if elev > 80:
                    self.ax.view_init(elev=80, azim=azim)
                elif elev < -80:
                    self.ax.view_init(elev=-80, azim=azim)
                    
                self.fig.canvas.draw_idle()
        
        self.fig.canvas.mpl_connect('key_press_event', on_key)
        self.fig.canvas.mpl_connect('motion_notify_event', on_motion)
        
        # Plot initial event
        self.plot_event()
        self._update_window_title()
        
        # Show initial help
        print("\n=== PhotonSim Visualization Controls ===")
        print("Arrow keys / N,P : Navigate events")
        print("Navigation buttons: Use mouse to click ← →")
        print("R                : Refresh view")
        print("Y                : Reset view (Y vertical)")
        print("0-9              : Jump to event number")
        print("H                : Show this help")
        print("Mouse            : Rotate, zoom, pan")
        print("========================================\n")
        
        plt.show()
    
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
        """Reset the 3D view to standard orientation with Y vertical."""
        self.ax.view_init(elev=15, azim=45)
        self.fig.canvas.draw()
    
    def _update_window_title(self):
        """Update the window title with current event info."""
        if hasattr(self, 'fig') and self.fig:
            event_data = self.get_event_data(self.current_event)
            if event_data:
                title = f"PhotonSim Event {event_data['event_id']}/{self.n_events-1}: "
                title += f"{event_data['primary_energy']:.1f} MeV, "
                title += f"{event_data['n_photons']:,} photons"
                self.fig.canvas.manager.set_window_title(title)
    
    def _show_help(self):
        """Display help information."""
        help_text = """
=== PhotonSim Visualization Controls ===
Arrow keys / N,P : Navigate between events
R                : Refresh current view  
0-9              : Jump to event number (0-9)
H                : Show this help
Mouse drag       : Rotate 3D view
Mouse wheel      : Zoom in/out
Mouse + Shift    : Pan view
========================================
        """
        print(help_text)
    
    def _create_jupyter_interface(self):
        """Create Jupyter notebook interface with widgets."""
        from ipywidgets import interact, IntSlider, Button, VBox, HBox, Output
        from IPython.display import display, clear_output
        
        # Event slider
        event_slider = IntSlider(
            value=0, min=0, max=self.n_events-1,
            description='Event:', style={'description_width': 'initial'}
        )
        
        # Navigation buttons
        prev_button = Button(description='Previous')
        next_button = Button(description='Next')
        
        # Output widget for plot
        output = Output()
        
        def update_plot(event_id):
            with output:
                clear_output(wait=True)
                self.goto_event(event_id)
                plt.show()
        
        def on_slider_change(change):
            update_plot(change['new'])
        
        def on_prev_click(b):
            if event_slider.value > 0:
                event_slider.value -= 1
        
        def on_next_click(b):
            if event_slider.value < self.n_events - 1:
                event_slider.value += 1
        
        # Connect events
        event_slider.observe(on_slider_change, names='value')
        prev_button.on_click(on_prev_click)
        next_button.on_click(on_next_click)
        
        # Layout
        controls = HBox([prev_button, event_slider, next_button])
        interface = VBox([controls, output])
        
        # Initial plot
        with output:
            self.plot_event()
            plt.show()
        
        display(interface)


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Visualize PhotonSim optical photon data')
    parser.add_argument('root_file', nargs='?', default='optical_photons.root',
                       help='Path to ROOT file (default: optical_photons.root)')
    parser.add_argument('--event', type=int, default=0,
                       help='Initial event to display (default: 0)')
    
    args = parser.parse_args()
    
    # Check if file exists
    import os
    if not os.path.exists(args.root_file):
        print(f"Error: ROOT file '{args.root_file}' not found")
        sys.exit(1)
    
    # Create visualizer
    print(f"Creating PhotonSim visualizer for {args.root_file}")
    visualizer = PhotonSimVisualizer(args.root_file)
    
    # Set initial event
    if args.event < visualizer.n_events:
        visualizer.current_event = args.event
    
    # Create interactive plot
    visualizer.create_interactive_plot()


if __name__ == "__main__":
    main()