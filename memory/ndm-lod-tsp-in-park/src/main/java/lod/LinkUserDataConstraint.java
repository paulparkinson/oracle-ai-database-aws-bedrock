package lod;

import java.util.Locale;

import oracle.spatial.network.lod.LODAnalysisInfo;
import oracle.spatial.network.lod.LODNetworkConstraint;
import oracle.spatial.network.lod.LogicalLink;
import oracle.spatial.network.lod.NetworkAnalyst;
import oracle.spatial.network.lod.UserData;

/**
 * Common implementation for link user-data constraints in THEME_PARK_NET.
 *
 * <p>The network registers ACCESSIBLE and COVERED as VARCHAR2 link user data
 * in category 0. Oracle exposes the values positionally within that category;
 * the current registration is ACCESSIBLE at index 0 and COVERED at index 1.</p>
 */
abstract class LinkUserDataConstraint implements LODNetworkConstraint {
    static final int USER_DATA_CATEGORY = 0;
    static final int ACCESSIBLE_INDEX = 0;
    static final int COVERED_INDEX = 1;

    private final String name;

    LinkUserDataConstraint(String name) {
        this.name = name;
    }

    @Override
    public final boolean isSatisfied(LODAnalysisInfo info) {
        if (info == null) {
            return false;
        }

        LogicalLink link = info.getNextLink();
        if (link == null) {
            return false;
        }

        UserData userData = link.getUserData(USER_DATA_CATEGORY);
        return userData != null && accepts(userData);
    }

    /** Returns whether the next link is allowed by this constraint. */
    protected abstract boolean accepts(UserData userData);

    protected static boolean isTrue(UserData userData, int index) {
        if (userData == null || index < 0 || index >= userData.getNumberOfUserData()) {
            return false;
        }

        Object value = userData.get(index);
        if (value instanceof Boolean) {
            return (Boolean) value;
        }

        if (value == null) {
            return false;
        }

        String normalized = value.toString().trim().toUpperCase(Locale.ROOT);
        return "TRUE".equals(normalized)
            || "T".equals(normalized)
            || "Y".equals(normalized)
            || "YES".equals(normalized)
            || "1".equals(normalized);
    }

    @Override
    public final int[] getUserDataCategories() {
        return new int[] {USER_DATA_CATEGORY};
    }

    @Override
    public final int getNumberOfUserObjects() {
        return 0;
    }

    @Override
    public final boolean isCurrentNodePartiallyExpanded(LODAnalysisInfo info) {
        return false;
    }

    @Override
    public final void reset() {
        // This constraint is stateless and can be reused by another analysis.
    }

    @Override
    public final void setNetworkAnalyst(NetworkAnalyst analyst) {
        // The constraint does not need to call back into the analyst.
    }

    @Override
    public final String toString() {
        return name;
    }

    /**
     * Creates the route constraint selected by the command-line examples.
     *
     * @param value NONE, ACCESSIBLE_ONLY, COVERED_ONLY, or BOTH; ACCESSIBLE and
     *              COVERED are accepted as aliases
     * @return null for NONE, otherwise the selected link constraint
     */
    static LODNetworkConstraint create(String value) {
        String normalized = value == null ? "NONE" : value.trim().toUpperCase(Locale.ROOT);
        switch (normalized) {
            case "NONE":
                return null;
            case "ACCESSIBLE":
            case "ACCESSIBLE_ONLY":
                return new AccessibleOnlyConstraint();
            case "COVERED":
            case "COVERED_ONLY":
                return new CoveredOnlyConstraint();
            case "BOTH":
                return new BothConstraint();
            default:
                throw new IllegalArgumentException(
                    "Unknown route constraint '" + value
                        + "'. Use NONE, ACCESSIBLE_ONLY, COVERED_ONLY, or BOTH.");
        }
    }
}
