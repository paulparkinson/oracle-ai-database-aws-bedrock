package lod;

import oracle.spatial.network.lod.UserData;

/** Allows only links that are both ACCESSIBLE and COVERED. */
public final class BothConstraint extends LinkUserDataConstraint {
    public BothConstraint() {
        super("ACCESSIBLE_AND_COVERED");
    }

    @Override
    protected boolean accepts(UserData userData) {
        return isTrue(userData, ACCESSIBLE_INDEX)
            && isTrue(userData, COVERED_INDEX);
    }
}
