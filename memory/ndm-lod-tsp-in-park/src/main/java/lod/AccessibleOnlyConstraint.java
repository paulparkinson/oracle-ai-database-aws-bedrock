package lod;

import oracle.spatial.network.lod.UserData;

/** Allows only links whose ACCESSIBLE user data value is true. */
public final class AccessibleOnlyConstraint extends LinkUserDataConstraint {
    public AccessibleOnlyConstraint() {
        super("ACCESSIBLE_ONLY");
    }

    @Override
    protected boolean accepts(UserData userData) {
        return isTrue(userData, ACCESSIBLE_INDEX);
    }
}
