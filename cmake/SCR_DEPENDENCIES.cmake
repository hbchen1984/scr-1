# This lists cmake logic to find dependencies in a file that
# is included in both CMakeLists.txt and dist/CMakeLists.txt.

## MPI
INCLUDE(SetupMPI)
IF(MPI_C_FOUND)
        INCLUDE_DIRECTORIES(${MPI_C_INCLUDE_PATH})
        LIST(APPEND SCR_EXTERNAL_LIBS ${MPI_C_LIBRARIES})
ELSE(MPI_C_FOUND)
        MESSAGE("WARNING: Could not find MPI!")
        MESSAGE("         Either add an MPI compiler to your path (using modules)")
        MESSAGE("         Or force CMake to build using the correct compiler (`export CC=mpicc`)")
ENDIF(MPI_C_FOUND)

## PMIx
IF(${SCR_RESOURCE_MANAGER} STREQUAL "PMIX")
	FIND_PACKAGE(PMIX REQUIRED)
	SET(HAVE_PMIX TRUE)
	INCLUDE_DIRECTORIES(${PMIX_INCLUDE_DIRS})
	LIST(APPEND SCR_EXTERNAL_LIBS ${PMIX_LIBRARIES})
ENDIF(${SCR_RESOURCE_MANAGER} STREQUAL "PMIX")

## CPPR
IF(ENABLE_INTEL_CPPR)
    FIND_PACKAGE(CPPR REQUIRED)
    SET(HAVE_CPPR TRUE)
    INCLUDE_DIRECTORIES(${CPPR_INCLUDE_DIRS})
    LIST(APPEND SCR_EXTERNAL_LIBS ${CPPR_LIBRARIES})
ENDIF(ENABLE_INTEL_CPPR)

## DataWarp
IF(ENABLE_CRAY_DW)
    FIND_PACKAGE(DataWarp REQUIRED)
    SET(HAVE_DATAWARP TRUE)
    INCLUDE_DIRECTORIES(${DATAWARP_INCLUDE_DIRS})
    LIST(APPEND SCR_EXTERNAL_LIBS ${DATAWARP_LIBRARIES})
    LIST(APPEND SCR_LINK_LINE " -L${WITH_DATAWARP_PREFIX}/lib64 -ldatawarp")
ENDIF(ENABLE_CRAY_DW)

## IBM Burst Buffer API
#IF(ENABLE_IBM_BBAPI)
#    FIND_PACKAGE(BBAPI)
#    IF(BBAPI_FOUND)
#        SET(HAVE_BBAPI TRUE)
#
#        SET(ENABLE_BBAPI_FALLBACK OFF CACHE BOOL "Fallback to a different transfer type if BBAPI not supported")
#        IF(${ENABLE_BBAPI_FALLBACK})
#            SET(HAVE_BBAPI_FALLBACK TRUE)
#        ENDIF(${ENABLE_BBAPI_FALLBACK})
#
#        INCLUDE_DIRECTORIES(${BBAPI_INCLUDE_DIRS})
#        LIST(APPEND SCR_EXTERNAL_LIBS ${BBAPI_LIBRARIES})
#        LIST(APPEND SCR_LINK_LINE " -L${WITH_BBAPI_PREFIX}/lib -lbbAPI")
#    ENDIF(BBAPI_FOUND)
#ENDIF(ENABLE_IBM_BBAPI)

## libyogrt
IF(ENABLE_YOGRT)
   FIND_PACKAGE(YOGRT QUIET)
   IF(YOGRT_FOUND)
      SET(HAVE_LIBYOGRT TRUE)
      INCLUDE_DIRECTORIES(${YOGRT_INCLUDE_DIRS})
      LIST(APPEND SCR_EXTERNAL_LIBS ${YOGRT_LIBRARIES})
      LIST(APPEND SCR_LINK_LINE " -L${WITH_YOGRT_PREFIX}/lib -lyogrt")
   ENDIF(YOGRT_FOUND)
ENDIF(ENABLE_YOGRT)

## mySQL
IF(ENABLE_MYSQL)
   FIND_PACKAGE(MySQL)
   IF(MYSQL_FOUND)
      SET(HAVE_LIBMYSQLCLIENT TRUE)
      INCLUDE_DIRECTORIES(${MYSQL_INCLUDE_DIRS})
      LIST(APPEND SCR_EXTERNAL_LIBS ${MYSQL_LIBRARIES})
      LIST(APPEND SCR_EXTERNAL_SERIAL_LIBS ${MYSQL_LIBRARIES})
      LIST(APPEND SCR_LINK_LINE " -L${WITH_MYSQL_PREFIX}/lib -lmysqlclient")
   ENDIF(MYSQL_FOUND)
ENDIF(ENABLE_MYSQL)

## ZLIB
FIND_PACKAGE(ZLIB REQUIRED)
IF(ZLIB_FOUND)
	INCLUDE_DIRECTORIES(${ZLIB_INCLUDE_DIRS})
	LIST(APPEND SCR_EXTERNAL_LIBS ${ZLIB_LIBRARIES})
	LIST(APPEND SCR_EXTERNAL_SERIAL_LIBS ${ZLIB_LIBRARIES})
	LIST(APPEND SCR_LINK_LINE "-lz")
ENDIF(ZLIB_FOUND)

# PTHREADS
FIND_PACKAGE(Threads REQUIRED)
IF(CMAKE_USE_PTHREADS_INIT)
	LIST(APPEND SCR_EXTERNAL_LIBS "-lpthread")
ENDIF()

## PDSH
IF(ENABLE_PDSH)
   IF(BUILD_PDSH)
      INCLUDE(ExternalProject)
      EXTERNALPROJECT_ADD(PDSH
         GIT_REPOSITORY    https://github.com/grondo/pdsh
         PREFIX            ${CMAKE_CURRENT_BINARY_DIR}/PDSH
         UPDATE_COMMAND    ${CMAKE_CURRENT_BINARY_DIR}/PDSH/src/PDSH/bootstrap
         CONFIGURE_COMMAND ${CMAKE_CURRENT_BINARY_DIR}/PDSH/src/PDSH/configure --prefix=${CMAKE_INSTALL_PREFIX}
         BUILD_COMMAND     ${MAKE}
      )
      SET(PDSH_EXE ${CMAKE_INSTALL_PREFIX}/bin/pdsh)
      SET(DSHBAK_EXE ${CMAKE_INSTALL_PREFIX}/bin/dshbak)
   ELSE(BUILD_PDSH)
      FIND_PACKAGE(PDSH REQUIRED)
   ENDIF(BUILD_PDSH)
ENDIF(ENABLE_PDSH)
