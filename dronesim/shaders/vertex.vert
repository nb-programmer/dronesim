#version 330 core

//Vertex data at location 0
layout(location = 0) in vec3 vtx_coord;
//Color data at location 1
//layout(location = 1) in vec3 vtx_color;

//Color for the fragment this vertex belongs to
out vec3 fragmentColor;

//Vertex data transformation matrix
uniform mat4 MVP;

void main() {
	gl_Position =  MVP * vec4(vtx_coord, 1);
	fragmentColor = vec3(1.0f, 0.0f, 0.0f);//vtx_color;
}
