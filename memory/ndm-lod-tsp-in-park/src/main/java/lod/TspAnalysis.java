package lod;

import java.io.InputStream;
import java.sql.Connection;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import oracle.spatial.network.lod.LODNetworkManager;
import oracle.spatial.network.lod.LogicalSubPath;
import oracle.spatial.network.lod.NetworkAnalyst;
import oracle.spatial.network.lod.NetworkIO;
import oracle.spatial.network.lod.PointOnNet;
import oracle.spatial.network.lod.SpatialSubPath;
import oracle.spatial.network.lod.TSP;
import oracle.spatial.network.lod.TspAnalysisInfo;
import oracle.spatial.network.lod.TspConstraint;
import oracle.spatial.network.lod.TspPath;
import oracle.spatial.network.lod.LODNetworkConstraint;
import oracle.spatial.network.lod.config.LODConfig;
import oracle.spatial.util.Logger;

/**
 * Minimal Oracle NDM LOD TSP example for park nodes.
 *
 * Each input node is represented as one PointOnNet candidate. The example uses
 * a closed tour by default and prints the visit order, leg costs, each leg
 * geometry, and the complete tour geometry as GeoJSON.
 */
public final class TspAnalysis {
    private TspAnalysis() {
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
        if (options.stopNodeIds.size() < 3) {
            throw new IllegalArgumentException("TSP requires at least three stop nodes.");
        }

        System.out.println("Network: " + options.networkName);
        System.out.println("DB user: " + options.dbUser);
        System.out.println("DB URL: " + options.dbUrl);
        System.out.println("Tour flag: " + options.tourFlag);
        System.out.println("Input stop nodes: " + options.stopNodeIds);
        System.out.println("Route constraint: " + options.routeConstraint);

        try (Connection connection = LODNetworkManager.getConnection(
                 options.dbUrl, options.dbUser, options.dbPassword)) {
            connection.setAutoCommit(false);
            loadLodConfig(options.configXmlFile, options.networkName);

            NetworkIO networkIO = LODNetworkManager.getCachedNetworkIO(
                connection, options.networkName, options.networkName, null);
            NetworkAnalyst analyst = LODNetworkManager.getNetworkAnalyst(networkIO);
            LODNetworkConstraint routeConstraint =
                LinkUserDataConstraint.create(options.routeConstraint);

            PointOnNet[][] pointsToVisit = new PointOnNet[options.stopNodeIds.size()][];
            for (int i = 0; i < options.stopNodeIds.size(); i++) {
                pointsToVisit[i] = new PointOnNet[] {
                    new PointOnNet(options.stopNodeIds.get(i))
                };
            }

            if (routeConstraint != null
                    && !hasCompletePairwisePaths(analyst, pointsToVisit, routeConstraint,
                        options.stopNodeIds)) {
                return;
            }

            TspPath tspPath;
            if (routeConstraint == null) {
                // Preserve the original default behavior when no route
                // constraint was requested.
                tspPath = analyst.tsp(pointsToVisit, options.tourFlag, null);
            } else {
                // TspImpl applies a supplied LODNetworkConstraint while it
                // builds pairwise shortest paths. If no TspConstraint is
                // supplied, it also reuses that link constraint while the
                // optimizer is choosing the visit order. That second use has
                // no current link and can make a valid constrained TSP fail.
                // Supply an allow-all TSP constraint so the link constraint
                // remains scoped to shortest-path expansion.
                tspPath = analyst.tsp(
                    pointsToVisit,
                    options.tourFlag,
                    routeConstraint,
                    new AllowAllTspConstraint());
            }

            printResult(networkIO, options.stopNodeIds, tspPath);
        }
    }

    private static void loadLodConfig(String configXmlFile, String networkName) throws Exception {
        try (InputStream config = TspAnalysis.class.getClassLoader()
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

    /**
     * TspImpl expects a complete pairwise cost matrix. Check it explicitly so
     * a disconnected constrained network is reported as an infeasible tour
     * instead of reaching TspImpl.getPaths with a null optimizer result.
     */
    private static boolean hasCompletePairwisePaths(
            NetworkAnalyst analyst,
            PointOnNet[][] pointsToVisit,
            LODNetworkConstraint routeConstraint,
            List<Long> nodeIds) throws Exception {
        for (int from = 0; from < pointsToVisit.length; from++) {
            for (int to = 0; to < pointsToVisit.length; to++) {
                if (from == to) {
                    continue;
                }

                boolean reachable = false;
                for (PointOnNet source : pointsToVisit[from]) {
                    for (PointOnNet target : pointsToVisit[to]) {
                        LogicalSubPath path = analyst.shortestPathDijkstra(
                            source, target, routeConstraint);
                        if (path != null && path.isFullPath()) {
                            reachable = true;
                            break;
                        }
                    }
                    if (reachable) {
                        break;
                    }
                }

                if (!reachable) {
                    System.out.println(
                        "No constrained path from node " + nodeIds.get(from)
                            + " to node " + nodeIds.get(to) + ".");
                    System.out.println(
                        "No feasible route found between the selected stops. "
                            + "TSP not executed.");
                    return false;
                }
            }
        }
        return true;
    }

    private static void printResult(
            NetworkIO networkIO, List<Long> inputNodeIds, TspPath tspPath) throws Exception {
        if (tspPath == null) {
            System.out.println("TSP returned no path.");
            return;
        }

        int[] order = tspPath.getTspOrder();
        double[] costs = tspPath.getCosts();
        LogicalSubPath[] paths = tspPath.getPaths();

        System.out.println("TSP input order indexes: " + Arrays.toString(order));
        System.out.println("TSP input node IDs in visit order:");
        for (int i = 0; i < order.length; i++) {
            int inputIndex = order[i];
            if (inputIndex >= 0 && inputIndex < inputNodeIds.size()) {
                System.out.println("  " + (i + 1) + ": node "
                    + inputNodeIds.get(inputIndex) + " (input index " + inputIndex + ")");
            } else {
                System.out.println("  " + (i + 1) + ": input index " + inputIndex);
            }
        }

        System.out.println("TSP leg count: " + (paths == null ? 0 : paths.length));
        if (costs != null) {
            System.out.println("TSP total cost by cost channel: " + Arrays.toString(costs));
        }

        if (paths == null) {
            return;
        }

        for (int i = 0; i < paths.length; i++) {
            LogicalSubPath path = paths[i];
            System.out.println("***** BEGIN TSP leg " + (i + 1) + " *****");
            if (path == null) {
                System.out.println("No subpath returned for this leg.");
            } else {
                System.out.println("Leg cost: " + path.getCost());
                if (path.getReferencePath() != null) {
                    System.out.println("  link IDs: "
                        + Arrays.toString(path.getReferencePath().getLinkIds()));
                    System.out.println("  node IDs: "
                        + Arrays.toString(path.getReferencePath().getNodeIds()));
                }

                SpatialSubPath spatialSubPath = networkIO.readSpatialSubPath(path);
                if (spatialSubPath != null && spatialSubPath.getGeometry() != null) {
                    System.out.println("  GeoJSON: "
                        + spatialSubPath.getGeometry().toGeoJson());
                } else {
                    System.out.println("  Spatial geometry is null.");
                }
            }
            System.out.println("***** END TSP leg " + (i + 1) + " *****");
        }

        printCompletePathGeoJson(networkIO, paths);
    }

    /**
     * Appends the TSP legs in visit order and asks NDM to rebuild one spatial
     * path. This preserves the network path semantics and avoids parsing and
     * concatenating the individual GeoJSON strings in application code.
     */
    private static void printCompletePathGeoJson(
            NetworkIO networkIO, LogicalSubPath[] paths) throws Exception {
        LogicalSubPath completePath = null;
        int appendedLegCount = 0;

        for (LogicalSubPath path : paths) {
            if (path == null) {
                continue;
            }

            completePath = completePath == null ? path : completePath.append(path);
            appendedLegCount++;
        }

        if (completePath == null) {
            System.out.println("No complete TSP path geometry returned.");
            return;
        }

        SpatialSubPath spatialCompletePath = networkIO.readSpatialSubPath(completePath);
        if (spatialCompletePath == null || spatialCompletePath.getGeometry() == null) {
            System.out.println("Complete TSP path geometry is null.");
            return;
        }

        System.out.println("***** BEGIN complete TSP path geometry GeoJSON *****");
        System.out.println("Complete path leg count: " + appendedLegCount);
        System.out.println(spatialCompletePath.getGeometry().toGeoJson());
        System.out.println("***** END complete TSP path geometry GeoJSON *****");
    }

    /** TSP-order constraint used to keep link filtering out of order selection. */
    private static final class AllowAllTspConstraint implements TspConstraint {
        @Override
        public boolean isSatisfied(TspAnalysisInfo info) {
            return true;
        }

        @Override
        public int[] getUserDataCategories() {
            return new int[0];
        }

        @Override
        public void reset() {
            // Stateless.
        }

        @Override
        public void setNetworkAnalyst(NetworkAnalyst analyst) {
            // No callback required.
        }
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
        private List<Long> stopNodeIds = new ArrayList<>(Arrays.asList(1L, 3L, 7L, 8L, 19L));
        private TSP.TourFlag tourFlag = TSP.TourFlag.CLOSED;
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
                    case "-stopNodeIds":
                        options.stopNodeIds = parseNodeIds(requireValue(args, ++i, argument));
                        break;
                    case "-tourFlag":
                        options.tourFlag = TSP.TourFlag.valueOf(
                            requireValue(args, ++i, argument).toUpperCase());
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

        private static List<Long> parseNodeIds(String value) {
            List<Long> nodeIds = new ArrayList<>();
            for (String token : value.split(",")) {
                String trimmed = token.trim();
                if (!trimmed.isEmpty()) {
                    nodeIds.add(Long.parseLong(trimmed));
                }
            }
            return nodeIds;
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
