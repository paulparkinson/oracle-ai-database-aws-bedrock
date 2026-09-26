package lod;

import oracle.spatial.network.lod.UserData;

/** Allows only links whose COVERED user data value is true. */
public final class CoveredOnlyConstraint extends LinkUserDataConstraint {
    public CoveredOnlyConstraint() {
        super("COVERED_ONLY");
    }

    @Override
    protected boolean accepts(UserData userData) {
        return isTrue(userData, COVERED_INDEX);
    }
}
