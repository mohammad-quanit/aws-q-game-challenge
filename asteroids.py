import pygame
import sys
import math
import random
import os
from pygame.locals import *

# Initialize Pygame
pygame.init()
pygame.mixer.init()  # Initialize sound mixer

# Game constants
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
GRAY = (169, 169, 169)

# Create the game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Asteroids")
clock = pygame.time.Clock()

# Asset paths
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# Function to load images safely
def load_image(filename, size=None):
    try:
        image_path = os.path.join(ASSETS_DIR, filename)
        if os.path.exists(image_path):
            image = pygame.image.load(image_path).convert_alpha()
            if size:
                image = pygame.transform.scale(image, size)
            return image
        else:
            print(f"Warning: Image {filename} not found at {image_path}")
            return None
    except pygame.error as e:
        print(f"Error loading image {filename}: {e}")
        return None

# Load sounds
try:
    shoot_sound = pygame.mixer.Sound("assets/laser.wav")
except:
    # Create a simple dummy sound object if file doesn't exist
    class DummySound:
        def play(self):
            pass
    shoot_sound = DummySound()
    print("Warning: assets/laser.wav not found, using silent sound")

# Create stars for background
stars = []
for _ in range(100):
    x = random.randint(0, WIDTH)
    y = random.randint(0, HEIGHT)
    size = random.randint(1, 2)
    speed = random.uniform(0.1, 0.3)  # Slow star movement
    stars.append([x, y, size, speed])

# Player spaceship class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Try to load spaceship image with larger size (60x75)
        self.original_image = load_image("spaceship.png", (60, 75))
        
        # If image loading fails, create a fallback shape
        if self.original_image is None:
            self.original_image = pygame.Surface((60, 75), pygame.SRCALPHA)
            
            # Main body of the ship
            pygame.draw.polygon(self.original_image, BLUE, [(30, 0), (0, 75), (60, 75)])
            
            # Cockpit
            pygame.draw.polygon(self.original_image, YELLOW, [(30, 15), (22, 45), (38, 45)])
            
            # Engines
            pygame.draw.rect(self.original_image, RED, (8, 67, 15, 8))
            pygame.draw.rect(self.original_image, RED, (37, 67, 15, 8))
            
            # Outline
            pygame.draw.polygon(self.original_image, WHITE, [(30, 0), (0, 75), (60, 75)], 1)
        
        self.image = self.original_image
        
        # Position at bottom center of screen, closer to the bottom
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 50))
        self.position = pygame.Vector2(WIDTH // 2, HEIGHT - 50)
        
        # Ship always points upward
        self.direction = pygame.Vector2(0, -1)
        self.velocity = pygame.Vector2(0, 0)
        self.speed = 5  # Horizontal movement speed
        
    def update(self):
        # Handle horizontal movement only
        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:
            self.velocity.x = -self.speed
        elif keys[K_RIGHT]:
            self.velocity.x = self.speed
        else:
            self.velocity.x = 0
            
        # Update position (horizontal only)
        self.position.x += self.velocity.x
        
        # Keep player within screen bounds
        if self.position.x < 20:
            self.position.x = 20
        elif self.position.x > WIDTH - 20:
            self.position.x = WIDTH - 20
            
        # Update rect position
        self.rect.center = (self.position.x, self.position.y)

    def shoot(self):
        # Play shooting sound
        shoot_sound.play()
        # Bullets always travel upward - adjust position based on new ship size
        return Bullet(self.position.x, self.position.y - 38, 0, -1)

# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy):
        super().__init__()
        self.image = pygame.Surface((4, 12))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x, y))
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(dx, dy) * 10  # Bullet speed
        self.lifetime = 60  # Frames the bullet will exist

    def update(self):
        self.position += self.velocity
        self.rect.center = self.position
        
        # Remove bullet when it goes off screen
        if self.position.y < 0:
            self.kill()
            
        # Decrease lifetime
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

# Asteroid class
class Asteroid(pygame.sprite.Sprite):
    def __init__(self, size=3, x=None, y=None):
        super().__init__()
        self.size = size
        
        # Size determines asteroid properties
        if size == 3:  # Large
            self.radius = 40
            self.speed = 1
            self.points = 20
            self.image_file = "asteroid_large.png"
        elif size == 2:  # Medium
            self.radius = 20
            self.speed = 2
            self.points = 50
            self.image_file = "asteroid_medium.png"
        else:  # Small
            self.radius = 10
            self.speed = 3
            self.points = 100
            self.image_file = "asteroid_small.png"
        
        # Try to load asteroid image
        self.original_image = load_image(self.image_file, (self.radius * 2, self.radius * 2))
        
        # If image loading fails, create a fallback shape
        if self.original_image is None:
            self.original_image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            
            # Create a more rock-like shape with more vertices and rougher edges
            points = []
            num_vertices = random.randint(8, 12)
            for i in range(num_vertices):
                angle = math.radians(i * (360 / num_vertices))
                # More variation in the distance for rougher edges
                distance = self.radius * random.uniform(0.7, 1.3)
                point_x = self.radius + math.cos(angle) * distance
                point_y = self.radius + math.sin(angle) * distance
                points.append((point_x, point_y))
            
            # Fill with rock color
            color = BROWN if size == 3 else GRAY
            pygame.draw.polygon(self.original_image, color, points)
            
            # Add some crater-like details
            for _ in range(3):
                crater_x = random.randint(self.radius//2, self.radius*3//2)
                crater_y = random.randint(self.radius//2, self.radius*3//2)
                crater_size = random.randint(2, self.radius//3)
                pygame.draw.circle(self.original_image, (color[0]//2, color[1]//2, color[2]//2), 
                                  (crater_x, crater_y), crater_size)
            
            # Add outline
            pygame.draw.polygon(self.original_image, WHITE, points, 1)
        
        self.image = self.original_image
        
        # Position the asteroid
        if x is None or y is None:
            # Spawn at the top of the screen with random x position
            x = random.randint(self.radius, WIDTH - self.radius)
            y = -self.radius * 2  # Start above the screen
        
        self.rect = self.image.get_rect(center=(x, y))
        self.position = pygame.Vector2(x, y)
        
        # Random downward direction
        angle = random.uniform(math.pi/4, math.pi*3/4)  # Downward with some variation
        self.velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * self.speed
        self.rotation = random.uniform(-3, 3)
        self.angle = 0

    def update(self):
        # Move asteroid
        self.position += self.velocity
        
        # Rotate asteroid
        self.angle += self.rotation
        rotated_image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = rotated_image.get_rect(center=self.position)
        self.image = rotated_image
        
        # Remove if it goes off the bottom of the screen
        if self.position.y > HEIGHT + self.radius:
            self.kill()
            
        self.rect.center = self.position

    def split(self):
        if self.size > 1:
            return [
                Asteroid(self.size - 1, self.position.x - 10, self.position.y),
                Asteroid(self.size - 1, self.position.x + 10, self.position.y)
            ]
        return []

# Game class
class Game:
    def __init__(self):
        self.player = Player()
        self.all_sprites = pygame.sprite.Group(self.player)
        self.bullets = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_over = False
        self.asteroid_spawn_timer = 0
        self.asteroid_spawn_delay = 120  # 2 seconds between asteroid spawns
        self.font = pygame.font.Font(None, 36)
        self.invulnerable = False
        self.invulnerable_timer = 0

    def spawn_asteroid(self):
        asteroid = Asteroid()
        self.asteroids.add(asteroid)
        self.all_sprites.add(asteroid)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_SPACE and not self.game_over:
                    bullet = self.player.shoot()
                    self.bullets.add(bullet)
                    self.all_sprites.add(bullet)
                elif event.key == K_r and self.game_over:
                    self.__init__()  # Reset the game
                elif event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    def update(self):
        if self.game_over:
            return
                
        # Check invulnerability
        if self.invulnerable:
            self.invulnerable_timer -= 1
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
                
        # Update all game objects
        self.all_sprites.update()
        
        # Spawn asteroids periodically
        self.asteroid_spawn_timer += 1
        if self.asteroid_spawn_timer >= self.asteroid_spawn_delay:
            self.spawn_asteroid()
            self.asteroid_spawn_timer = 0
            # Decrease spawn delay as level increases (more frequent asteroids)
            self.asteroid_spawn_delay = max(30, 120 - (self.level * 10))
        
        # Check for collisions between bullets and asteroids
        hits = pygame.sprite.groupcollide(self.bullets, self.asteroids, True, True)
        for bullet, asteroids_hit in hits.items():
            for asteroid in asteroids_hit:
                self.score += asteroid.points
                # Split asteroid into smaller ones
                for new_asteroid in asteroid.split():
                    self.asteroids.add(new_asteroid)
                    self.all_sprites.add(new_asteroid)
        
        # Check for collisions between player and asteroids
        if not self.invulnerable:
            hits = pygame.sprite.spritecollide(self.player, self.asteroids, True, pygame.sprite.collide_circle)
            if hits:
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
                else:
                    self.invulnerable = True
                    self.invulnerable_timer = 180  # 3 seconds of invulnerability
        
        # Level up every 500 points
        if self.score >= self.level * 500:
            self.level += 1
            
        # Update stars
        for star in stars:
            star[1] += star[3]  # Move stars down slowly
            if star[1] > HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, WIDTH)

    def draw(self):
        screen.fill(BLACK)
        
        # Draw stars in the background
        for star in stars:
            pygame.draw.circle(screen, WHITE, (int(star[0]), int(star[1])), star[2])
        
        # Draw all sprites
        for sprite in self.all_sprites:
            if sprite != self.player:
                screen.blit(sprite.image, sprite.rect)
        
        # Draw player with blinking effect when invulnerable
        if not self.invulnerable or self.invulnerable_timer % 30 < 15:
            screen.blit(self.player.image, self.player.rect)
        
        # Draw score and lives
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        screen.blit(lives_text, (10, 50))
        
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        screen.blit(level_text, (WIDTH - 150, 10))
        
        # Draw game over screen
        if self.game_over:
            game_over_text = self.font.render("GAME OVER", True, RED)
            restart_text = self.font.render("Press R to restart", True, WHITE)
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))
        
        pygame.display.flip()

# Main game loop
def main():
    # Check if assets directory exists
    if not os.path.exists(ASSETS_DIR):
        print(f"Creating assets directory at {ASSETS_DIR}")
        os.makedirs(ASSETS_DIR, exist_ok=True)
        print("Please add spaceship.png, asteroid_large.png, asteroid_medium.png, and asteroid_small.png to the assets folder")
    
    game = Game()
    
    # Show instructions
    screen.fill(BLACK)
    font = pygame.font.Font(None, 36)
    title = font.render("ASTEROIDS", True, WHITE)
    instructions = [
        "Left/Right arrows to move",
        "Space to shoot",
        "Destroy asteroids to score points",
        "Press any key to start"
    ]
    
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
    
    for i, line in enumerate(instructions):
        text = font.render(line, True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 + i * 40))
    
    pygame.display.flip()
    
    # Wait for key press
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                waiting = False
    
    # Main game loop
    while True:
        game.handle_events()
        game.update()
        game.draw()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
