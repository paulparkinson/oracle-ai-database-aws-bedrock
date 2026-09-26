package lod;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

import oracle.spatial.network.lod.LODNetworkManager;

/** Lightweight wallet/JDBC and network metadata check. */
public final class DbConnectionCheck {
    private DbConnectionCheck() {
    }

    public static void main(String[] args) throws Exception {
        String dbUrl = "";
        String dbUser = "ADVENTURE_KINGDOM";
        String dbPassword = firstNonBlank(
            System.getenv("DB_PASSWORD"), System.getenv("ORACLE_PASSWORD"));
        String networkName = "THEME_PARK_NET";

        for (int i = 0; i < args.length; i++) {
            String argument = args[i];
            switch (argument) {
                case "-dbUrl":
                    dbUrl = requireValue(args, ++i, argument);
                    break;
                case "-dbUser":
                    dbUser = requireValue(args, ++i, argument);
                    break;
                case "-dbPassword":
                    dbPassword = requireValue(args, ++i, argument);
                    break;
                case "-networkName":
                    networkName = requireValue(args, ++i, argument).toUpperCase();
                    break;
                default:
                    throw new IllegalArgumentException("Unknown option: " + argument);
            }
        }

        if (dbUrl.isBlank()) {
            throw new IllegalArgumentException("Missing -dbUrl.");
        }
        if (dbPassword == null || dbPassword.isBlank()) {
            throw new IllegalArgumentException("Missing DB password. Use -PdbPassword or DB_PASSWORD.");
        }

        try (Connection connection = LODNetworkManager.getConnection(dbUrl, dbUser, dbPassword)) {
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
                        System.out.println("No metadata row found for " + networkName);
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
