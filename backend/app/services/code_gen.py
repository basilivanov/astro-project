# ############################################################################
# AI_HEADER: MODULE_CODE_GENERATOR
# ROLE: Generate unique referral codes.
# DEPENDENCIES: random, string
# GRACE_ANCHORS: [CODE_GEN]
# ############################################################################

import random
import string

def generate_referral_code(length=6) -> str:
    """
    # PURPOSE: Generate a short random alphanumeric string.
    # INPUT: length.
    # OUTPUT: string like '8kz2a'.
    """
    chars = string.ascii_lowercase + string.digits
    return 'u_' + ''.join(random.choices(chars, k=length))
