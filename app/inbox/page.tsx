'use client';
import Inbox from '../terminal/Inbox';import {useWorkspace} from '../workspace/Workspace';
export default function Page(){const {research}=useWorkspace();return <Inbox onResearch={research} dedicated/>}
