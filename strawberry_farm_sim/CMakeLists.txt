cmake_minimum_required(VERSION 3.8)
project(strawberry_farm_sim)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch worlds config
  DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/generate_world.py
  DESTINATION lib/${PROJECT_NAME})

ament_package()
