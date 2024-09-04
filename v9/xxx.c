ULONG slsp_cli_ParseIngressLsp(IN VOID *pCfgMsg)
{
    IF_SELECT_S stSelect;
    CHAR   szIfName[IF_MAX_NAME_LEN+1];
    SLSP_CFG_S stSlsp;
    in_addr_t *pDestAddr = NULL;
    UINT   uiBlkSeqNo = 0;
    UINT   uiMOR  = 0;
    UINT   uiMask = 0;
    UINT   uiMaskLen = 0;
    IF_INDEX ifIndexOut = IF_INVALID_INDEX;
    BOOL_T bOutIntf  = BOOL_FALSE;
    BOOL_T bIfType   = BOOL_FALSE;
    BOOL_T bUndoFlag = BOOL_FALSE;


    /* 获取配置消息中的MOR信息 */
    memset(&stSlsp, 0, sizeof(SLSP_CFG_S));
    stSlsp.uiInLabel = LSM_INVALID_LABEL;
    pDestAddr = &(stSlsp.stDestAddr.s_addr);

    szIfFullName[0] = '\\0';
	TSN_DBM_PROC_NODE_S *pstProcNode = NULL;
    ULONG ulErrCode = ERROR_SUCCESS;
//	DTQ_FOREACH_ENTRY(&g_stTSNDbmProcList, pstProcNode, stNode)
//    {
//        if (NULL == pstProcNode->stRegInfo.pfCfgProcFunc)
//        {
//            continue;
//        }
//
//        ulErrCode |= pstProcNode->stRegInfo.pfCfgProcFunc(g_hTSNUsedCfgDbmHandle, g_hTSNUnusedCfgDbmHandle);
//    }


//    MOR_ScanParaFromMsg(pCfgMsg, uiBlkSeqNo, uiMOR, pParaInfo)
//    {
//        switch (uiMOR)
//        {
//            case MOR_SLSP_INGRESS_NAME:
//            {
//                /* 获取lsp-name */
//                (VOID)MOR_GetDataFromPara(pParaInfo, SLSP_MAX_LSPNAME_NEW_LENGTH + 1, stSlsp.szLspName);
//                stSlsp.enLspType = SLSP_TYPE_INGRESS;
//                break;
//            }
//            case MOR_SLSP_INGRESS_DESTADDR:
//            {
//                /* 获取dest-address */
//                *pDestAddr = htonl(MOR_GetData32(pParaInfo));
//                break;
//            }
//            default:
//            {
//                /* 不能识别的OID */
//                DBGASSERT(0);
//                break;
//            }
//        }
//    }

    /* 判断是否是二阶段生效模式do操作 */
    ulView = getCurrentViewMode();

    /* 如果配置出接口 */
    if(BOOL_TRUE == bOutIntf)
    {
        /* 如果是if type类型,组装成接口名字 */
        if (BOOL_TRUE == bIfType)
        {
            szIfFullName[0] = '\\0';
            (VOID)scnprintf(szIfFullName, IF_MAX_NAME_LEN + 1, \"%s%s\", szIfFullType, szIfNum);
        }

        ifIndexOut = IF_GetIfIndexByFullName(szIfFullName);
        if (IF_INVALID_INDEX == ifIndexOut)
        {
            return ERROR_SUCCESS;
        }
        stSlsp.ifIndexOut = ifIndexOut;
        (VOID)strlcpy(stSlsp.szIfName, szIfFullName, sizeof(stSlsp.szIfName));
        /* 如果配置的是出接口，必须将标志位置为出接口 */
        BIT_SET(stSlsp.ucFlag, SLSP_CFGIFOUT);

        pcTemp = strstr(szIfFullName, \"Tunnel\");
        if (NULL != pcTemp)
        {
            if ((COMSH_VIEW_PRIVATE_MODE == ulView) || (COMSH_VIEW_EXCLUSIVE_MODE == ulView))
            {
                if (1 == sscanf(szIfFullName, \"Tunnel%u\", &uiTunnelNum))
                {
                    (VOID)TUNNEL_GetMode4Commit(uiTunnelNum, &uiTunnelMode);
                    enTnlMode = (TUNNEL_MODE_E)uiTunnelMode;
                }
            }
            else
            {
                (VOID)TUNNEL_GetMode(ifIndexOut, &enTnlMode);
            }
            if ((TUNNEL_MODE_IPV4_GRE != enTnlMode) && (TUNNEL_MODE_CR_LSP != enTnlMode))
            {
                return IDS_SLSP_ERROR_NO_SUPPORT;
            }
        }
    }

	while(usLoop > 0)
    {
        for(usCount = 0; usCount < usLoop; usCount++)
        {
          pstMsgHead = (TUNNELFIB_MSG_HEAD_S *)pcMsgData;
          pcMsgData = pcMsgData + TUNNELFIB_MSG_HEAD_LEN;
          ulMsgDataLen = TUNNELFIB_MSG_EncodeData(ucOperType, ucMsgType, pcMsg, usMsgBufLen, pcMsgData);
          if(0 == ulMsgDataLen)  /*buf空间不足*/
          {
            break;
          }
          TUNNELFIB_MSG_EncodeHead(ucOperType, ucMsgType, ulMsgDataLen, ERROR_SUCCESS, pstMsgHead);
          ulMsgLen += TUNNELFIB_MSG_HEAD_LEN + ulMsgDataLen; /*计算写入总长度*/
          pcMsgData += ulMsgDataLen;/*偏移buf指针*/
          usMsgBufLen = (usMsgBufLen - TUNNELFIB_MSG_HEAD_LEN) - (USHORT)ulMsgDataLen; /*计算剩余buf空间*/
          pcMsg += usMsgNodeSize;  /*对消息进行偏移*/
        }

        if (ulMsgLen != (ULONG)send(iSocketFd, acMsgBuf, ulMsgLen, MSG_DONTWAIT))
        {
            return ERROR_FAILED;
        }
        ulRet = TUNNELFIB_MSG_RecvMsg(iSocketFd, pOutData);
        usLoop -= usCount;
        pcMsgData = acMsgBuf;   /*发送缓冲区清零*/
        ulMsgLen = 0;
        ulMsgDataLen = 0;
        usMsgBufLen = TUNNELFIB_MSG_MAX_LEN;    /*发送缓冲区剩余长度初始化*/
        pstMsgHead = NULL;
    }

	for(; uiIndex < TUNNELFIB_DBG_MAX_NUM; uiIndex++)
    {
        stDebugInfo.auiDebugError[uiIndex] = htonl(pstDebugInfo->auiDebugError[uiIndex]);
        stDebugInfo.auiDebugEvent[uiIndex] = htonl(pstDebugInfo->auiDebugEvent[uiIndex]);
    }


    /* 将Destination地址和掩码进行与操作 */
    uiMask = htonl(uiMask);
    *pDestAddr = (*pDestAddr) & (uiMask);

	TUNNELFIB_DBG_PrintDbg(TUNNELFIB_DBG_PACKET,
                        pcInfo,
                        szIfName,
                        szSrc,
                        szDest,
                        uiPktLenFinal);

    if ((COMSH_VIEW_PRIVATE_MODE == ulView) || (COMSH_VIEW_EXCLUSIVE_MODE == ulView))
    {
        return SLSP_COMMIT_ProcStaticLsp(bUndoFlag, &stSlsp);
    }

	/* 模拟两行注释,
       这是第二行 */
    uiEmbedSrcAddr = TUNN4_6O4_GETEMBEDIPV4ADDR(&(pstIP6->stIp6Src),
                                                 pstCoreData->ucIPv6PrefixLen,
                                                 INET_ADDR_IP4ADDRUINT(&(pstCoreData->stSrcAddr)),
                                                 pstCoreData->ucIPv4PrefixLen,
                                                 pstCoreData->ucIPv4SuffixLen);

    return SLSP_SetStaticLsp(bUndoFlag, &stSlsp);
}