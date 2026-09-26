package lod;

import java.io.InputStream;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Arrays;

import oracle.spatial.network.lod.LODNetworkManager;
import oracle.spatial.network.lod.LODNetworkConstraint;
import oracle.spatial.network.lod.LogicalSubPath;
import oracle.spatial.network.lod.NetworkAnalyst;
import oracle.spatial.network.lod.NetworkIO;
import oracle.spatial.network.lod.PointOnNet;
import oracle.spatial.network.lod.SpatialSubPath;
import oracle.spatial.network.lod.config.LODConfig;
import oracle.spatial.network.lod.util.PrintUtility;
import oracle.spatial.util.Logger;

/** Minimal smoke test for the THEME_PARK_NET Oracle NDM network. */
public final class ShortestPathAnalysis {
    private ShortestPathAnalysis() {
    }

    public static void main(String[] args) throws Exception {
        Options options = Options.parse(args);
        setLogLevel(options.logLevel);

        if (options.dbUrl.isBlank()) {
            throw new IllegalArgumentException(
                "Missing -dbUrl. The Gradle task supplies a wallet URL by default.");
        }
        if (options.dbPassword == null || options.dbPassword.isBlank()) {
            throw new IllegalArgumentException(
                "Missing DB password. Use -PdbPassword or DB_PASSWORD.");
        }

        System.out.println("Network: " + options.networkName);
        System.out.println("DB user: " + options.dbUser);
        System.out.println("DB URL: " + options.dbUrl);
        System.out.println("Start node: " + options.startNodeId);
        System.out.println("End node: " + options.endNodeId);
        System.out.println("Route constraint: " + options.routeConstraint);

        try (Connection connection = LODNetworkManager.getConnection(
                 options.dbUrl, options.dbUser, options.dbPassword)) {
            connection.setAutoCommit(false);
            printConnectionAndMetadata(connection, options.networkName);
            loadLodConfig(options.configXmlFile, options.networkName);

            NetworkIO networkIO = LODNetworkManager.getCachedNetworkIO(
                connection, options.networkName, options.networkName, null);
            NetworkAnalyst analyst = LODNetworkManager.getNetworkAnalyst(networkIO);
            LODNetworkConstraint routeConstraint =
                LinkUserDataConstraint.create(options.routeConstraint);

            System.out.println("***** BEGIN shortestPathDijkstra *****");
            LogicalSubPath subPath = analyst.shortestPathDijkstra(
                new PointOnNet(options.startNodeId),
                new PointOnNet(options.endNodeId),
                routeConstraint);

            printSubPath(subPath);
            printSpatialSubPathGeoJson(networkIO, subPath);
            System.out.println("***** END shortestPathDijkstra *****");
        }
    }

    private static void loadLodConfig(String configXmlFile, String networkName) throws Exception {
        try (InputStream config = ShortestPathAnalysis.class.getClassLoader()
                 .getResourceAsStream(configXmlFile)) {
            if (config == null) {
                throw new IllegalArgumentException(
                    "Cannot find LOD config resource: " + configXmlFile);
            }

            LODNetworkManager.getConfigManager().loadConfig(config);
            LODConfig lodConfig = LODNetworkManager.getConfigManager().getConfig(networkName);
            if (lodConfig == null) {
                System.out.println(
                    "No explicit LOD config found for " + networkName
                        + "; the default NDM configuration will be used.");
            }
        }
    }

    private static void printConnectionAndMetadata(Connection connection, String networkName)
            throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement("select user from dual");
             ResultSet resultSet = statement.executeQuery()) {
            if (resultSet.next()) {
                System.out.println("Connected as: " + resultSet.getString(1));
            }
        }

        String sql = "select network, network_category, link_direction, "
            + "no_of_hierarchy_levels, no_of_partitions, node_table_name, "
            + "link_table_name, path_table_name "
            + "from user_sdo_network_metadata where network = ?";

        try (PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, networkName);
            try (ResultSet resultSet = statement.executeQuery()) {
                if (!resultSet.next()) {
                    System.out.println("No USER_SDO_NETWORK_METADATA row found.");
                    return;
                }

                System.out.println("Network metadata:");
                System.out.println("  network=" + resultSet.getString("NETWORK"));
                System.out.println("  category=" + resultSet.getString("NETWORK_CATEGORY"));
                System.out.println("  direction=" + resultSet.getString("LINK_DIRECTION"));
                System.out.println("  hierarchy_levels="
                    + resultSet.getString("NO_OF_HIERARCHY_LEVELS"));
                System.out.println("  partitions=" + resultSet.getString("NO_OF_PARTITIONS"));
                System.out.println("  node_table=" + resultSet.getString("NODE_TABLE_NAME"));
                System.out.println("  link_table=" + resultSet.getString("LINK_TABLE_NAME"));
                System.out.println("  path_table=" + resultSet.getString("PATH_TABLE_NAME"));
            }
        }
    }

    private static void printSubPath(LogicalSubPath subPath) {
        if (subPath == null) {
            System.out.println("No path returned.");
            return;
        }

        System.out.println("Is full path: " + subPath.isFullPath());
        System.out.println("Cost: " + subPath.getCost());
        if (subPath.getReferencePath() != null) {
            long[] linkIds = subPath.getReferencePath().getLinkIds();
            long[] nodeIds = subPath.getReferencePath().getNodeIds();
            System.out.println("Link count: " + (linkIds == null ? 0 : linkIds.length));
            System.out.println("Node count: " + (nodeIds == null ? 0 : nodeIds.length));
            System.out.println("Link IDs: " + Arrays.toString(linkIds));
            System.out.println("Node IDs: " + Arrays.toString(nodeIds));
        }
        PrintUtility.print(System.out, subPath, true, 20, 0);
    }

    private static void printSpatialSubPathGeoJson(NetworkIO networkIO, LogicalSubPath subPath)
            throws Exception {
        if (subPath == null) {
            return;
        }

        SpatialSubPath spatialSubPath = networkIO.readSpatialSubPath(subPath);
        if (spatialSubPath == null || spatialSubPath.getGeometry() == null) {
            System.out.println("Spatial subpath geometry is null.");
            return;
        }

        System.out.println("***** BEGIN path geometry GeoJSON *****");
        System.out.println(spatialSubPath.getGeometry().toGeoJson());
        System.out.println("***** END path geometry GeoJSON *****");
    }

    private static void setLogLevel(String logLevel) {
        if ("FATAL".equalsIgnoreCase(logLevel)) {
            Logger.setGlobalLevel(Logger.LEVEL_FATAL);
        } else if ("ERROR".equalsIgnoreCase(logLevel)) {
            Logger.setGlobalLevel(Logger.LEVEL_ERROR);
        } else if ("WARN".equalsIgnoreCase(logLevel)) {
            Logger.setGlobalLevel(Logger.LEVEL_WARN);
        } else if ("INFO".equalsIgnoreCase(logLevel)) {
            Logger.setGlobalLevel(Logger.LEVEL_INFO);
        } else if ("DEBUG".equalsIgnoreCase(logLevel)) {
            Logger.setGlobalLevel(Logger.LEVEL_DEBUG);
        } else if ("FINEST".equalsIgnoreCase(logLevel)) {
            Logger.setGlobalLevel(Logger.LEVEL_FINEST);
        } else {
            Logger.setGlobalLevel(Logger.LEVEL_ERROR);
        }
    }

    private static final class Options {
        private String dbUrl = "";
        private String dbUser = "ADVENTURE_KINGDOM";
        private String dbPassword = firstNonBlank(
            System.getenv("DB_PASSWORD"), System.getenv("ORACLE_PASSWORD"));
        private String networkName = "THEME_PARK_NET";
        private long startNodeId = 1L;
        private long endNodeId = 3L;
        private String routeConstraint = "NONE";
        private String configXmlFile = "lod/LODConfigs.xml";
        private String logLevel = "ERROR";

        private static Options parse(String[] args) {
            Options options = new Options();
            for (int i = 0; i < args.length; i++) {
                String argument = args[i];
                switch (argument) {
                    case "-dbUrl":
                        options.dbUrl = requireValue(args, ++i, argument);
                        break;
                    case "-dbUser":
                        options.dbUser = requireValue(args, ++i, argument);
                        break;
                    case "-dbPassword":
                        options.dbPassword = requireValue(args, ++i, argument);
                        break;
                    case "-networkName":
                        options.networkName = requireValue(args, ++i, argument).toUpperCase();
                        break;
                    case "-startNodeId":
                        options.startNodeId = Long.parseLong(requireValue(args, ++i, argument));
                        break;
                    case "-endNodeId":
                        options.endNodeId = Long.parseLong(requireValue(args, ++i, argument));
                        break;
                    case "-routeConstraint":
                        options.routeConstraint = requireValue(args, ++i, argument);
                        break;
                    case "-configXmlFile":
                        options.configXmlFile = requireValue(args, ++i, argument);
                        break;
                    case "-logLevel":
                        options.logLevel = requireValue(args, ++i, argument);
                        break;
                    default:
                        throw new IllegalArgumentException("Unknown option: " + argument);
                }
            }
            return options;
        }

        private static String requireValue(String[] args, int index, String option) {
            if (index >= args.length) {
                throw new IllegalArgumentException("Missing value for " + option);
            }
            return args[index];
        }

        private static String firstNonBlank(String... values) {
            for (String value : values) {
                if (value != null && !value.isBlank()) {
                    return value;
                }
            }
            return null;
        }
    }
}
