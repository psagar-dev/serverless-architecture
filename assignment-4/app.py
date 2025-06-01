import boto3
import os
from datetime import datetime, timezone, timedelta

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    
    # Environment variables (required: EBS_VOLUME_ID, RETENTION_DAYS)
    volume_id = os.environ.get('EBS_VOLUME_ID', "vol-012af92482dff76bd")
    retention_days = int(os.environ.get('RETENTION_DAYS', '0'))  # Default 30 days

    if not volume_id:
        raise ValueError("Missing required environment variable: EBS_VOLUME_ID")

    # 1. Create Snapshot
    try:
        desc = f"Automated backup of {volume_id} @ {datetime.now(timezone.utc).isoformat()}"
        snap = ec2.create_snapshot(VolumeId=volume_id, Description=desc)
        created_snap_id = snap['SnapshotId']
        print(f"✅ Created snapshot: {created_snap_id}")
    except Exception as e:
        print(f"❌ Snapshot creation failed: {e}")
        raise

    # 2. Delete Old Snapshots
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted_snaps = []
    try:
        snaps = get_completed_snapshots(ec2, volume_id)

        for snapshot in snaps:
            snap_id = snapshot['SnapshotId']
            start_time = snapshot['StartTime']
            if start_time < cutoff:
                try:
                    ec2.delete_snapshot(SnapshotId=snap_id)
                    deleted_snaps.append(snap_id)
                    print(f"🗑️ Deleted old snapshot: {snap_id}")
                except Exception as delete_err:
                    print(f"❌ Failed to delete snapshot {snap_id}: {delete_err}")

        if not deleted_snaps:
            print("✅ No old snapshots to delete.")

    except Exception as e:
        print(f"❌ Snapshot cleanup failed: {e}")
        raise

    return {
        "created_snapshot": created_snap_id,
        "deleted_snapshots": deleted_snaps
    }

def get_completed_snapshots(ec2, volume_id):
    """Return all completed snapshots for a given EBS volume, owned by this account."""
    try:
        response = ec2.describe_snapshots(
            Filters=[
                {'Name': 'volume-id', 'Values': [volume_id]},
                {'Name': 'status', 'Values': ['completed']}
            ],
            OwnerIds=['self']
        )
        snapshots = response.get('Snapshots', [])
        
        return snapshots
    except Exception as e:
        return []