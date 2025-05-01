import pygame
import os
import config

# Define tile types
EMPTY = 0
WALL = 1  # Unbreakable wall
BRICK = 2  # Breakable wall/brick

class Level:
    def __init__(self, filename=None):
        self.grid = []
        self.width = 0
        self.height = 0
        # Load images
        self.images = {
            EMPTY: pygame.Surface((config.GRID_SIZE, config.GRID_SIZE)),
            WALL: pygame.Surface((config.GRID_SIZE, config.GRID_SIZE)),
            BRICK: pygame.Surface((config.GRID_SIZE, config.GRID_SIZE))
        }
        
        # Set default colors for the tiles if images can't be loaded
        self.images[EMPTY].fill((50, 205, 50))  # Light green floor
        self.images[WALL].fill((100, 100, 100))  # Gray wall
        self.images[BRICK].fill((165, 42, 42))  # Brown brick
        
        # Try to load images if they exist
        try:
            # The paths should be adjusted to your project structure
            # Since you have a 'photos' folder in your project
            self.images[EMPTY] = pygame.image.load("photos/floor.png").convert_alpha()
            self.images[WALL] = pygame.image.load("photos/wall.png").convert_alpha()
            self.images[BRICK] = pygame.image.load("photos/brick.png").convert_alpha()
            
            # Scale images to match grid size
            for key in self.images:
                self.images[key] = pygame.transform.scale(self.images[key], 
                                                         (config.GRID_SIZE, config.GRID_SIZE))
        except pygame.error as e:
            print(f"Warning: Could not load images for level rendering: {e}")
            print("Using colored rectangles instead.")

        # Load the level if filename is provided
        if filename:
            self.load_level(filename)

    def load_level(self, filename):
        """Load a level from a text file."""
        try:
            self.grid = []
            with open(filename, 'r') as f:
                lines = f.readlines()
                
                for line in lines:
                    # Remove any whitespace and newline characters
                    line = line.strip()
                    if line:  # Skip empty lines
                        row = [int(cell) for cell in line if cell.isdigit()]
                        self.grid.append(row)
            
            # Update level dimensions
            if self.grid:
                self.height = len(self.grid)
                self.width = len(self.grid[0])
                
            return True
        except FileNotFoundError:
            print(f"Error: Level file '{filename}' not found.")
            return False
        except Exception as e:
            print(f"Error loading level: {e}")
            return False
    
    def draw(self, screen):
        """Draw the level grid on the screen."""
        for row_idx, row in enumerate(self.grid):
            for col_idx, tile_type in enumerate(row):
                x = col_idx * config.GRID_SIZE
                y = row_idx * config.GRID_SIZE
                
                # Draw the appropriate tile image
                if tile_type in self.images:
                    screen.blit(self.images[tile_type], (x, y))
                else:
                    # Fallback for unknown tile types
                    pygame.draw.rect(screen, (255, 0, 255), (x, y, config.GRID_SIZE, config.GRID_SIZE))
    
    def is_valid_position(self, x, y):
        """Check if the given grid position is valid and empty."""
        grid_x = x // config.GRID_SIZE
        grid_y = y // config.GRID_SIZE
        
        # Check boundaries
        if grid_x < 0 or grid_x >= self.width or grid_y < 0 or grid_y >= self.height:
            return False
        
        # Check if the position is empty
        return self.grid[grid_y][grid_x] == EMPTY
    
    def get_tile_type(self, x, y):
        """Get the tile type at the given pixel position."""
        grid_x = x // config.GRID_SIZE
        grid_y = y // config.GRID_SIZE
        
        # Check boundaries
        if grid_x < 0 or grid_x >= self.width or grid_y < 0 or grid_y >= self.height:
            return -1  # Out of bounds
        
        return self.grid[grid_y][grid_x]
    
    def set_tile(self, x, y, tile_type):
        """Set a tile at the given grid position."""
        if 0 <= y < self.height and 0 <= x < self.width:
            self.grid[y][x] = tile_type
    
    def generate_standard_level(self, width=15, height=13):
        """Generate a standard Bomberman level with walls in a grid pattern."""
        self.width = width
        self.height = height
        self.grid = []
        
        for y in range(height):
            row = []
            for x in range(width):
                # Place walls in a grid pattern (every other tile)
                if x == 0 or y == 0 or x == width-1 or y == height-1:
                    # Border walls
                    row.append(WALL)
                elif x % 2 == 0 and y % 2 == 0:
                    # Interior permanent walls
                    row.append(WALL)
                else:
                    # Empty space or randomly place bricks
                    import random
                    if random.random() < 0.7:  # 70% chance for a brick
                        row.append(BRICK)
                    else:
                        row.append(EMPTY)
            self.grid.append(row)
        
        # Ensure the corners near the player spawn are empty
        # (standard in Bomberman to give players space)
        self.grid[1][1] = EMPTY
        self.grid[1][2] = EMPTY
        self.grid[2][1] = EMPTY
        
        # For player 2 (if multiplayer)
        self.grid[height-2][width-2] = EMPTY
        self.grid[height-2][width-3] = EMPTY
        self.grid[height-3][width-2] = EMPTY