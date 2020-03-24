FROM debian:jessie

LABEL maintainer = "Dmitry Zarva <zarv1k@gmail.com>"

ARG steam_user
ARG steam_password
ARG amxmod_version

RUN useradd -ms /bin/bash cstrike

RUN apt-get update && apt-get install -y lib32gcc1 curl unzip && rm -rf /var/lib/apt/lists/* && chown cstrike:cstrike /opt

USER cstrike

# Install SteamCMD
RUN mkdir -p /opt/steam /opt/hlds && cd /opt/steam && \
    curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar zxvf -

# Install HLDS
# Workaround for "app_update 90" bug, see https://forums.alliedmods.net/showthread.php?p=2518786
RUN /opt/steam/steamcmd.sh +login $steam_user $steam_password +force_install_dir /opt/hlds +app_update 90 validate +quit; \
    /opt/steam/steamcmd.sh +login $steam_user $steam_password +force_install_dir /opt/hlds +app_update 70 validate +quit || \
    /opt/steam/steamcmd.sh +login $steam_user $steam_password +force_install_dir /opt/hlds +app_update 10 validate +quit || \
    /opt/steam/steamcmd.sh +login $steam_user $steam_password +force_install_dir /opt/hlds +app_update 90 validate +quit
RUN mkdir -p ~/.steam && ln -s /opt/hlds ~/.steam/sdk32 && ln -s /opt/steam/ /opt/hlds/steamcmd
COPY --chown=cstrike:cstrike image/steam_appid.txt /opt/hlds/steam_appid.txt

# Install metamod
RUN mkdir -p /opt/hlds/cstrike/addons/metamod/dlls
COPY --chown=cstrike:cstrike mod/metamod /opt/hlds/cstrike/addons/metamod/dlls
COPY --chown=cstrike:cstrike image/liblist.gam /opt/hlds/cstrike/liblist.gam

# Install AMX mod X
RUN curl -sqL "http://www.amxmodx.org/release/amxmodx-$amxmod_version-base-linux.tar.gz" | tar -C /opt/hlds/cstrike/ -zxvf -
RUN curl -sqL "http://www.amxmodx.org/release/amxmodx-$amxmod_version-cstrike-linux.tar.gz" | tar -C /opt/hlds/cstrike/ -zxvf -

# Install dproto
RUN mkdir -p /opt/hlds/cstrike/addons/dproto
COPY --chown=cstrike:cstrike mod/dproto/dproto_i386.so /opt/hlds/cstrike/addons/dproto/dproto_i386.so

USER root
RUN apt-get remove -y curl unzip && apt-get autoremove -y
USER cstrike

# Install Deathbeams AMX plugin
COPY --chown=cstrike:cstrike mod/deathbeams/deathbeams.amxx /opt/hlds/cstrike/addons/amxmodx/plugins/deathbeams.amxx

# Install HeadShot Only AMX Plugin
COPY --chown=cstrike:cstrike mod/hsonly/hsonly.sma /opt/hlds/cstrike/addons/amxmodx/scripting/hsonly.sma
COPY --chown=cstrike:cstrike mod/hsonly/hsonly.amxx /opt/hlds/cstrike/addons/amxmodx/plugins/hsonly.amxx
COPY --chown=cstrike:cstrike mod/hsonly/hs_only.txt /opt/hlds/cstrike/addons/amxmodx/data/lang/hs_only.txt

# Install YaPB Bots
COPY --chown=cstrike:cstrike mod/yapb /opt/hlds/cstrike/addons/yapb
COPY --chown=cstrike:cstrike mod/yapbmenu/amxx_yapbmenu.sma /opt/hlds/cstrike/addons/amxmodx/scripting/amxx_yapbmenu.sma
COPY --chown=cstrike:cstrike mod/yapbmenu/amxx_yapbmenu.amxx /opt/hlds/cstrike/addons/amxmodx/plugins/amxx_yapbmenu.amxx

# Enable plugins
COPY --chown=cstrike:cstrike image/plugins.ini /opt/hlds/cstrike/addons/metamod/plugins.ini

# Dproto config
COPY --chown=cstrike:cstrike mod/dproto/dproto.cfg /opt/hlds/cstrike/dproto.cfg

# Add maps
COPY --chown=cstrike:cstrike maps/* /opt/hlds/cstrike/maps/
COPY --chown=cstrike:cstrike config/mapcycle.txt /opt/hlds/cstrike/mapcycle.txt
COPY --chown=cstrike:cstrike config/maps.ini /opt/hlds/cstrike/addons/amxmodx/configs/maps.ini

# Add default server config
COPY --chown=cstrike:cstrike config/server.cfg /opt/hlds/cstrike/server.cfg

# Add Entrypoint script
COPY --chown=cstrike:cstrike hlds_run.sh /bin/hlds_run.sh

WORKDIR /opt/hlds

ENTRYPOINT ["/bin/hlds_run.sh"]
