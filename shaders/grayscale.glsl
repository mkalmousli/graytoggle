#version 330

in vec2 texcoord;
uniform sampler2D tex;

// Provided by picom (declared here so the linker knows it exists)
vec4 default_post_processing(vec4 c);

vec4 window_shader() {
    vec2 texsize = textureSize(tex, 0);
    vec4 c = texture2D(tex, texcoord / texsize, 0);

    float g = dot(c.rgb, vec3(0.2126, 0.7152, 0.0722));
    c.rgb = vec3(g);

    return default_post_processing(c);
}
