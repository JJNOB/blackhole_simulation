# Gravitational lensing: background distortion (simple)
def draw_background(ctx, prog, proj, view):
    # Draw a quad with a lensing shader
    vertices = np.array([
        -40, -40, 0.0,
         40, -40, 0.0,
         40,  40, 0.0,
        -40,  40, 0.0,
    ], dtype='f4')
    vbo = ctx.buffer(vertices)
    vao = ctx.simple_vertex_array(prog, vbo, 'in_vert')
    prog['model'].write(Matrix44.identity().astype('f4').tobytes())
    prog['view'].write(view.astype('f4').tobytes())
    prog['proj'].write(proj.astype('f4').tobytes())
    vao.render(moderngl.TRIANGLE_FAN)

vertex_shader_bg = '''
#version 330
in vec3 in_vert;
uniform mat4 model;
uniform mat4 view;
uniform mat4 proj;
out vec2 uv;
void main() {
    gl_Position = proj * view * model * vec4(in_vert, 1.0);
    uv = in_vert.xy * 0.0125 + 0.5;
}
'''

fragment_shader_bg = '''
#version 330
in vec2 uv;
out vec4 fragColor;
void main() {
    float r = length(uv - vec2(0.5, 0.5));
    float lens = 1.0 / (1.0 + 20.0 * pow(r, 3.0));
    vec3 col = mix(vec3(0.1, 0.1, 0.15), vec3(0.0, 0.0, 0.0), lens);
    fragColor = vec4(col, 1.0);
}
'''
import numpy as np
import moderngl
import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from pyrr import Matrix44, Vector3

# Simulation parameters
g = 6.67430e-11  # Gravitational constant
blackhole_mass = 1e31  # Mass of black hole (kg)
star_mass = 1e30  # Mass of star (kg)
star_pos = np.array([0.0, 0.0, 10.0])
star_vel = np.array([0.0, 0.0, -0.1])

# Camera parameters
camera_pos = Vector3([0.0, 0.0, 20.0])
camera_front = Vector3([0.0, 0.0, -1.0])
camera_up = Vector3([0.0, 1.0, 0.0])

# Window setup
def init_window():
    pygame.init()
    pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Black Hole Simulation")
    ctx = moderngl.create_context()
    return ctx

# Simple sphere rendering (for black hole/star)
def create_sphere(ctx, radius=1.0, color=(1.0, 1.0, 1.0, 1.0)):
    # Placeholder: use a simple quad for now
    vertices = np.array([
        -radius, -radius, 0.0,
         radius, -radius, 0.0,
         radius,  radius, 0.0,
        -radius,  radius, 0.0,
    ], dtype='f4')
    colors = np.array(list(color) * 4, dtype='f4')
    vbo = ctx.buffer(vertices)
    cbo = ctx.buffer(colors)
    prog = ctx.program(vertex_shader=vertex_shader_sphere, fragment_shader=fragment_shader_sphere)
    vao = ctx.vertex_array(prog, [(vbo, '3f', 'in_vert'), (cbo, '4f', 'in_color')])
    return vao, prog

vertex_shader = '''
#version 330
in vec3 in_vert;
uniform mat4 model;
uniform mat4 view;
uniform mat4 proj;
void main() {
    gl_Position = proj * view * model * vec4(in_vert, 1.0);
}
'''

fragment_shader = '''
#version 330
out vec4 fragColor;
# Utility: create a ring (photon ring)
void main() {
    fragColor = vec4(0.0, 0.0, 0.0, 1.0); // Black for black hole
}
'''

vertex_shader_sphere = '''
#version 330
in vec3 in_vert;
in vec4 in_color;
uniform mat4 model;
uniform mat4 view;
uniform mat4 proj;
out vec4 v_color;
void main() {
    gl_Position = proj * view * model * vec4(in_vert, 1.0);
    v_color = in_color;
}
'''

fragment_shader_sphere = '''
#version 330
in vec4 v_color;
out vec4 fragColor;
void main() {
    fragColor = v_color;
}
'''

vertex_shader_disk = '''
#version 330
in vec3 in_vert;
in vec4 in_color;
uniform mat4 model;
uniform mat4 view;
uniform mat4 proj;
out vec4 v_color;
void main() {
    gl_Position = proj * view * model * vec4(in_vert, 1.0);
    v_color = in_color;
}
'''

fragment_shader_disk = '''
#version 330
in vec4 v_color;
out vec4 fragColor;
void main() {
    fragColor = v_color;
}
'''

fragment_shader_ring = '''
#version 330
in vec4 v_color;
out vec4 fragColor;
void main() {
    fragColor = v_color * 1.5;
}
'''

# Main loop
def main():
    ctx = init_window()
    clock = pygame.time.Clock()
    running = True

    # Create objects
    blackhole, prog_bh = create_sphere(ctx, radius=2.0, color=(0.0, 0.0, 0.0, 1.0))
    star, prog_star = create_sphere(ctx, radius=1.0, color=(1.0, 1.0, 0.7, 1.0))
    disk, prog_disk = create_disk(ctx)
    ring, prog_ring = create_ring(ctx)
    prog_bg = ctx.program(vertex_shader=vertex_shader_bg, fragment_shader=fragment_shader_bg)

    # Camera matrices
    proj = Matrix44.perspective_projection(45.0, 800/600, 0.1, 100.0)
    view = Matrix44.look_at(camera_pos, camera_pos + camera_front, camera_up)


    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Camera movement (WASD)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    camera_pos += camera_front * 0.5
                if event.key == pygame.K_s:
                    camera_pos -= camera_front * 0.5
                if event.key == pygame.K_a:
                    camera_pos -= Vector3.cross(camera_front, camera_up) * 0.5
                if event.key == pygame.K_d:
                    camera_pos += Vector3.cross(camera_front, camera_up) * 0.5

        # Physics update (star falling toward black hole)
        r = np.linalg.norm(star_pos)
        force = -g * blackhole_mass * star_mass / (r**2)
        acc = force / star_mass * (star_pos / r)
        star_vel += acc * 0.01
        star_pos += star_vel * 0.01

        # Update camera view
        view = Matrix44.look_at(camera_pos, camera_pos + camera_front, camera_up)

        ctx.clear(0.1, 0.1, 0.15)
        # Draw background with lensing
        draw_background(ctx, prog_bg, proj, view)
        # Draw accretion disk
        prog_disk['model'].write(Matrix44.identity().astype('f4').tobytes())
        prog_disk['view'].write(view.astype('f4').tobytes())
        prog_disk['proj'].write(proj.astype('f4').tobytes())
        disk.render(moderngl.TRIANGLE_FAN)
        # Draw photon ring
        prog_ring['model'].write(Matrix44.identity().astype('f4').tobytes())
        prog_ring['view'].write(view.astype('f4').tobytes())
        prog_ring['proj'].write(proj.astype('f4').tobytes())
        ring.render(moderngl.TRIANGLE_FAN)
        # Draw black hole
        prog_bh['model'].write(Matrix44.identity().astype('f4').tobytes())
        prog_bh['view'].write(view.astype('f4').tobytes())
        prog_bh['proj'].write(proj.astype('f4').tobytes())
        blackhole.render(moderngl.TRIANGLE_FAN)
        # Draw star
        model_star = Matrix44.from_translation(star_pos)
        prog_star['model'].write(model_star.astype('f4').tobytes())
        prog_star['view'].write(view.astype('f4').tobytes())
        prog_star['proj'].write(proj.astype('f4').tobytes())
        star.render(moderngl.TRIANGLE_FAN)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
