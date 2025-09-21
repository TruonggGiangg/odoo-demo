def migrate(cr, version):
    """Add new columns to p2p_loan table"""
    # Add contractId column
    cr.execute("""
        ALTER TABLE p2p_loan 
        ADD COLUMN IF NOT EXISTS "contractId" VARCHAR
    """)
    
    # Add new fields
    cr.execute("""
        ALTER TABLE p2p_loan 
        ADD COLUMN IF NOT EXISTS "willing" TEXT
    """)
    
    cr.execute("""
        ALTER TABLE p2p_loan 
        ADD COLUMN IF NOT EXISTS "maturity_date" DATE
    """)
    
    cr.execute("""
        ALTER TABLE p2p_loan 
        ADD COLUMN IF NOT EXISTS "created_date" DATE
    """)
    
    cr.execute("""
        ALTER TABLE p2p_loan 
        ADD COLUMN IF NOT EXISTS "monthly_principal_pay" NUMERIC
    """)
    
    cr.execute("""
        ALTER TABLE p2p_loan 
        ADD COLUMN IF NOT EXISTS "monthly_interest_pay" NUMERIC
    """)
    
    cr.execute("""
        ALTER TABLE p2p_loan 
        ADD COLUMN IF NOT EXISTS "monthly_pay" NUMERIC
    """)
    
    cr.execute("""
        ALTER TABLE p2p_loan 
        ADD COLUMN IF NOT EXISTS "entirely_pay" NUMERIC
    """)
    
    cr.execute("""
        ALTER TABLE p2p_loan 
        ADD COLUMN IF NOT EXISTS "total_notes" INTEGER
    """)
    
    cr.execute("""
        ALTER TABLE p2p_loan 
        ADD COLUMN IF NOT EXISTS "invested_notes" INTEGER
    """)
    
    # Update existing records to have contractId = loan_id if contractId is null
    cr.execute("""
        UPDATE p2p_loan 
        SET "contractId" = loan_id 
        WHERE "contractId" IS NULL OR "contractId" = ''
    """)
