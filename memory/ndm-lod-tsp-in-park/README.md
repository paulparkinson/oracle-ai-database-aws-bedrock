# NDM LOD TSP in Park

This Gradle project tests Dijkstra shortest path and TSP against the
`THEME_PARK_NET` Oracle Spatial Network Data Model network. The network must be
created in the target Oracle schema before running the Java examples. The
source GeoJSON, splitting script, and NDM setup SQL are included in this
repository.

The project downloads the Oracle JDBC, Spatial, and Network Data Model jars
from the internal Oracle Artifactory into a local `libs/` directory. The jar
files are ignored by Git and are not committed to this repository. An
Artifactory read token is not required for the currently published jar URLs.
If an environment or future artifact requires authentication, the token is
read from `ARTIFACTORY_TOKEN`, `PHX_ARTIFACTORY_READER_TOKEN`,
`-PartifactoryToken`, or the matching property in `~/.gradle/gradle.properties`.

The Oracle wallet is not included in this repository. Obtain a wallet zip and
pass its path to `prepareWallet` or the run task.
The zip is expanded by `prepareWallet` into:

```text
wallet/
```

The default JDBC `TNS_ADMIN` points to the local `wallet/` directory. The
database password is never stored in this project.

The wallet directory and wallet archives are ignored by Git.

## Prepare wallet

Use a wallet zip obtained separately from this repository. The path can be
passed to any task that uses the wallet:

```bash
./gradlew prepareWallet --no-daemon \
  -PwalletZip='/secure/path/to/Wallet.zip'
```

If `wallet/` already contains `tnsnames.ora`, `sqlnet.ora`, and `cwallet.sso`,
the run tasks detect the prepared wallet and skip zip extraction. In that case,
`-PwalletZip` is not required.

## Build

The current artifact URLs support anonymous downloads, so no token is needed
for the normal build:

```bash
./gradlew build --no-daemon
```

If your environment requires Artifactory authentication, set a read token:

```bash
export ARTIFACTORY_TOKEN='your_artifactory_read_token'
```

Alternatively, add this property to `~/.gradle/gradle.properties`:

```properties
artifactoryToken=your_artifactory_read_token
```

Then build as usual:

```bash
./gradlew build --no-daemon
```

The build automatically runs `downloadOracleJars` before compiling. To run the
download explicitly or force a refresh:

```bash
./gradlew downloadOracleJars --no-daemon
./gradlew downloadOracleJars --no-daemon --rerun-tasks
```

The default artifact versions are `ojdbc11`/`oraclepki`
`26.1.0.24.0.260902`, `sdoapi`/`sdoutl` `251003_main`, and `sdonm`
`23.1.0_20230601`. The repository URLs and versions can be overridden with
`-PjdbcArtifactoryUrl`, `-PspatialArtifactoryUrl`, `-PoracleJdbcVersion`,
`-PoracleSpatialVersion`, and `-PoracleNdmVersion`.

## Prepare source network data

The mixed GeoJSON contains both node and link features. Split it into the two
GeoJSON files expected by the SQL setup script:

```bash
python3 scripts/split_theme_park_network.py
```

The default input is:

```text
data/theme_park_network.geojson
```

Generated files are written to `data/generated/`:

```text
data/generated/theme_park_network_nodes.geojson
data/generated/theme_park_network_links.geojson
data/generated/id_mapping.csv
```

Load the generated node and link GeoJSON files into the source tables
`THEME_PARK_NETWORK_NODES` and `THEME_PARK_NETWORK_LINKS`, then run:

```text
sql/process.sql
```

The SQL script creates and validates the one-level `THEME_PARK_NET` network,
including the `ACCESSIBLE` and `COVERED` link user-data columns.
https://docs.oracle.com/en/database/oracle/oracle-database/26/topol/main-steps-using-network-data-model-graph.html

## Check wallet connection and network registration

```bash
DB_PASSWORD='your_password' ./gradlew checkDbConnection --no-daemon \
  -PwalletZip='/secure/path/to/Wallet.zip'
```

Defaults:

```text
DB user:    ADVENTURE_KINGDOM
DB service: mbrjr0nifb76c6lr_low
network:    THEME_PARK_NET
wallet:     wallet/ (created locally; not committed)
```

## Run shortest path

The default test computes an accessible-only path from node `22` to node `21`:

```bash
DB_PASSWORD='your_password' ./gradlew runShortestPath --no-daemon \
  -PstartNodeId='22' \
  -PendNodeId='21' \
  -ProuteConstraint='ACCESSIBLE_ONLY'
```

Equivalent explicit invocation:

```bash
./gradlew runShortestPath --no-daemon \
  -PdbUser='ADVENTURE_KINGDOM' \
  -PdbPassword='your_password' \
  -PwalletZip='/secure/path/to/Wallet.zip' \
  -PdbService='mbrjr0nifb76c6lr_low' \
  -PnetworkName='THEME_PARK_NET' \
  -PstartNodeId='22' \
  -PendNodeId='21' \
  -ProuteConstraint='ACCESSIBLE_ONLY'
```

The program prints database/network metadata, path cost, ordered node/link IDs,
and the returned spatial subpath as GeoJSON.

Supported route constraints are `NONE`, `ACCESSIBLE_ONLY`, `COVERED_ONLY`, and
`BOTH`. `BOTH` requires both `ACCESSIBLE` and `COVERED` to be true on every
link in the route. The values are read from link user-data category `0`.

Useful properties include `dbUrl`, `dbService`, `tnsAdmin`, `walletDir`,
`walletZip`, `javaVersion`, and `logLevel`.

## Run TSP

The default open tour keeps node `14` as the fixed start and visits nodes `19`,
`21`, `22`, and `23`:

```bash
DB_PASSWORD='your_password' ./gradlew runTsp --no-daemon \
  -PstopNodeIds='14,19,21,22,23' \
  -PtourFlag='OPEN_FIXED_START'
```

Specify a different set of stop nodes with a comma-separated list:

```bash
DB_PASSWORD='your_password' ./gradlew runTsp --no-daemon \
  -PwalletZip='/secure/path/to/Wallet.zip' \
  -PstopNodeIds='14,19,21,22,23,25' \
  -PtourFlag='OPEN_FIXED_START' \
  -ProuteConstraint='ACCESSIBLE_ONLY'
```

Supported tour flags are `CLOSED`, `OPEN`, `OPEN_FIXED_START`,
`OPEN_FIXED_END`, and `OPEN_FIXED_START_END`. The TSP example prints the visit
order, leg costs, total cost, link/node IDs, and each leg's GeoJSON geometry.

When a route constraint is selected, it is applied to every pairwise shortest
path used by TSP. The example checks that all selected stops are pairwise
reachable under that constraint before invoking TSP optimizer; if a
constrained leg is unavailable, it reports that no complete constrained tour
can be built for the selected stops.
